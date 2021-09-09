import logging
import time

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.did import did_to_id
from common_utils_py.exceptions import (
    InvalidAgreementTemplate,
    InvalidServiceAgreementSignature,
    ServiceAgreementExists,
)
from contracts_lib_py.utils import add_ethereum_prefix_and_hash_msg
from contracts_lib_py.web3_provider import Web3Provider

from nevermined_sdk_py.agreement_events.access_agreement import consume_asset, refund_reward
from nevermined_sdk_py.agreement_events.compute_agreement import execute_computation
from nevermined_sdk_py.agreement_events.payments import \
    fulfillLockRewardCondition
from nevermined_sdk_py.nevermined.conditions import Conditions
from web3 import Web3

logger = logging.getLogger(__name__)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'


def check_token_address(keeper, token_address):
    if token_address == '0x0' or token_address == ZERO_ADDRESS:
        return ZERO_ADDRESS
    elif not Web3.isAddress(token_address):
        return keeper.token.address
    return token_address


class Agreements:
    """Nevermined agreements class."""

    def __init__(self, keeper, asset_resolver, asset_consumer, asset_executor, config):
        self._keeper = keeper
        self._asset_resolver = asset_resolver
        self._asset_consumer = asset_consumer
        self._asset_executor = asset_executor
        self._config = config
        self.conditions = Conditions(self._keeper)

    def prepare(self, did, consumer_account, service_index):
        """

        :param did: str representation fo the asset DID. Use this to retrieve the asset DDO.
        :param consumer_account: Account instance of the consumer
        :param service_index: int identifies the specific service in
         the ddo to use in this agreement.
        :return: tuple (agreement_id: str, signature: hex str)
        """
        agreement_id = ServiceAgreement.create_new_agreement_id()
        signature = self._sign(agreement_id, did, consumer_account, service_index)
        return agreement_id, signature

    def create(self, did, index, agreement_id, consumer_address, account):
        """
        Execute the service agreement on-chain using keeper's ServiceAgreement contract.

        The on-chain executeAgreement method requires the following arguments:
        templateId, signature, consumer, hashes, timeouts, serviceAgreementId, did.
        `agreement_message_hash` is necessary to verify the signature.
        The consumer `signature` includes the conditions timeouts and parameters values which
        is usedon-chain to verify that the values actually match the signed hashes.

        :param did: str representation fo the asset DID. Use this to retrieve the asset DDO.
        :param index: str identifies the specific service in
         the ddo to use in this agreement.
        :param agreement_id: 32 bytes identifier created by the consumer and will be used
         on-chain for the executed agreement.
         conditions and their parameters values and other details of the agreement.
        :param consumer_address: ethereum account address of consumer, hex str
        :param account: Account instance creating the agreement. Can be either the
            consumer, publisher or provider
        :return: dict the `executeAgreement` transaction receipt
        """
        assert consumer_address and Web3Provider.get_web3().isChecksumAddress(
            consumer_address), f'Invalid consumer address {consumer_address}'

        payment_involved = True
        asset = self._asset_resolver.resolve(did)
        asset_id = asset.asset_id
        service = asset.get_service_by_index(index)
        if service.type == ServiceTypes.ASSET_ACCESS:
            agreement_template = self._keeper.access_template
            template_address = self._keeper.access_template.address
        elif service.type == ServiceTypes.CLOUD_COMPUTE:
            agreement_template = self._keeper.escrow_compute_execution_template
            template_address = self._keeper.escrow_compute_execution_template.address
        elif service.type == ServiceTypes.NFT_SALES:
            agreement_template = self._keeper.nft_sales_template
            template_address = self._keeper.nft_sales_template.address
        elif service.type == ServiceTypes.NFT_ACCESS:
            payment_involved = False
            agreement_template = self._keeper.nft_access_template
            template_address = self._keeper.nft_access_template.address
        else:
            raise Exception('The agreement could not be created. Review the index of your service.')

        agreement_template_approved = self._keeper.template_manager.is_template_approved(template_address)
        if not agreement_template_approved:
            msg = (f'The Service Agreement Template contract at address '
                   f'{template_address} is not '
                   f'approved and cannot be used for creating service agreements.')
            logger.warning(msg)
            raise InvalidAgreementTemplate(msg)

        if agreement_template.get_agreement_consumer(agreement_id) != ZERO_ADDRESS:
            raise ServiceAgreementExists(
                f'Service agreement {agreement_id} already exists, cannot reuse '
                f'the same agreement id.')

        service_agreement = ServiceAgreement.from_service_index(index, asset)
        token_address = check_token_address(
            self._keeper, service_agreement.get_param_value_by_name('_tokenAddress'))

        publisher_address = Web3Provider.get_web3().toChecksumAddress(asset.publisher)
        condition_ids = service_agreement.generate_agreement_condition_ids(
            agreement_id, asset_id, consumer_address, self._keeper, token_address=token_address)

        time_locks = service_agreement.conditions_timelocks
        time_outs = service_agreement.conditions_timeouts

        if payment_involved and service_agreement.get_price() > self._keeper.token.get_token_balance(consumer_address):
            return Exception(
                f'The consumer balance is '
                f'{self._keeper.token.get_token_balance(consumer_address)}. '
                f'This balance is lower that the asset price {service_agreement.get_price()}.')

        if service.type == ServiceTypes.NFT_SALES:
            conditions_ordered = [condition_ids[1], condition_ids[0], condition_ids[2]]
        elif service.type == ServiceTypes.NFT_ACCESS:
            conditions_ordered = [condition_ids[1], condition_ids[0]]
        else:
            conditions_ordered = condition_ids

        success = agreement_template.create_agreement(
            agreement_id,
            asset_id,
            conditions_ordered,
            time_locks,
            time_outs,
            consumer_address,
            account
        )

        if success:
            if payment_involved:
                self.conditions.lock_payment(
                    agreement_id,
                    asset_id,
                    service_agreement.get_amounts_int(),
                    service_agreement.get_receivers(),
                    token_address,
                    account)
                return self._is_condition_fulfilled(agreement_id, 'lockReward')
            return True
        return False

    def status(self, agreement_id):
        """
        Get the status of a service agreement.

        :param agreement_id: id of the agreement, hex str
        :return: dict with condition status of each of the agreement's conditions or None if the
        agreement is invalid.
        """
        condition_ids = self._keeper.agreement_manager.get_agreement(agreement_id).condition_ids
        result = {"agreementId": agreement_id}
        conditions = dict()
        for i in condition_ids:
            conditions[self._keeper.get_condition_name_by_address(
                self._keeper.condition_manager.get_condition(
                    i).type_ref)] = self._keeper.condition_manager.get_condition_state(i)
        result["conditions"] = conditions
        return result

    def is_access_granted(self, agreement_id, did, consumer_address):
        """
        Check permission for the agreement.

        Verify on-chain that the `consumer_address` has permission to access the given asset `did`
        according to the `agreement_id`.

        :param agreement_id: id of the agreement, hex str
        :param did: DID, str
        :param consumer_address: ethereum account address of consumer, hex str
        :return: bool True if user has permission
        """
        agreement_consumer = self._keeper.access_template.get_agreement_consumer(
            agreement_id)

        if agreement_consumer is None:
            return False

        if agreement_consumer != consumer_address:
            logger.warning(f'Invalid consumer address {consumer_address} and/or '
                           f'service agreement id {agreement_id} (did {did})'
                           f', agreement consumer is {agreement_consumer}')
            return False

        document_id = did_to_id(did)
        return self._keeper.access_condition.check_permissions(
            document_id, consumer_address
        )

    def _sign(self, agreement_id, did, consumer_account, service_index):
        """
        Sign a service agreement.

        :param agreement_id: 32 bytes identifier created by the consumer and will be used
         on-chain for the executed agreement.
        :param did: str representation fo the asset DID. Use this to retrieve the asset DDO.
        :param consumer_account: Account instance of the consumer
        :param service_index: int identifies the specific service in
         the ddo to use in this agreement.
        :return: signature
        """
        asset = self._asset_resolver.resolve(did)
        service_agreement = asset.get_service_by_index(service_index)

        publisher_address = self._keeper.did_registry.get_did_owner(asset.asset_id)
        agreement_hash = service_agreement.get_service_agreement_hash(
            agreement_id, asset.asset_id, consumer_account.address, publisher_address, self._keeper
        )
        signature = self._keeper.sign_hash(add_ethereum_prefix_and_hash_msg(agreement_hash),
                                           consumer_account)
        address = self._keeper.personal_ec_recover(agreement_hash, signature)
        assert address == consumer_account.address
        logger.debug(f'agreement-signature={signature}, agreement-hash={agreement_hash}')
        return signature

    def _is_condition_fulfilled(self, agreement_id, condition_type):
        # TODO move this method to the contracts-lib-py
        max_retries = 5
        sleep_time = 500
        iteration = 0
        while iteration < max_retries:
            status = self.status(agreement_id)
            condition_status = status.get('conditions').get(condition_type)
            logger.debug(f'Condition check[  ${condition_type}  ] : + ${condition_status}')
            if condition_status == 2:
                return True
            iteration = iteration + 1
            time.sleep(sleep_time)

        return False

    def _process_consumer_agreement_events(
            self, agreement_id, did, service_agreement, account,
            condition_ids, publisher_address, from_block, auto_consume, agreement_type):
        logger.debug(
            f'process consumer events for agreement {agreement_id}, blockNumber {from_block + 10}')
        if agreement_type == ServiceTypes.ASSET_ACCESS:
            self._keeper.access_template.subscribe_agreement_created(
                agreement_id,
                300,
                fulfillLockRewardCondition,
                (agreement_id, service_agreement.get_price(), account, condition_ids[1]),
                from_block=from_block
            )
        else:
            self._keeper.escrow_compute_execution_template.subscribe_agreement_created(
                agreement_id,
                300,
                fulfillLockRewardCondition,
                (agreement_id, service_agreement.get_price(), account, condition_ids[1]),
                from_block=from_block
            )

        if auto_consume:
            def _refund_callback(_price, _publisher_address, _condition_ids):
                def do_refund(_event, _agreement_id, _did, _service_agreement, _consumer_account,
                              *_):
                    refund_reward(
                        _event, _agreement_id, _did, _service_agreement, _price,
                        _consumer_account, _publisher_address, _condition_ids, _condition_ids[2]
                    )

                return do_refund

            conditions_dict = service_agreement.condition_by_name
            if agreement_type == ServiceTypes.ASSET_ACCESS:
                self._keeper.access_condition.subscribe_condition_fulfilled(
                    agreement_id,
                    max(conditions_dict['accessSecretStore'].timeout, 300),
                    consume_asset,
                    (agreement_id, did, service_agreement, account, self._asset_consumer.download,
                     self._config.secret_store_url, self._config.parity_url,
                     self._config.downloads_path),
                    timeout_callback=_refund_callback(
                        service_agreement.get_price(), publisher_address, condition_ids
                    ),
                    from_block=from_block
                )
            else:
                self._keeper.compute_execution_condition.subscribe_condition_fulfilled(
                    agreement_id,
                    max(conditions_dict['execCompute'].timeout, 300),
                    execute_computation,
                    (agreement_id, did, service_agreement, account, self._asset_executor.execute),
                    timeout_callback=_refund_callback(
                        service_agreement.get_price(), publisher_address, condition_ids
                    ),
                    from_block=from_block
                )

    def _log_agreement_info(self, asset, service_agreement, agreement_id, agreement_signature,
                            consumer_address, publisher_account, condition_ids):
        agreement_hash = service_agreement.get_service_agreement_hash(
            agreement_id, asset.asset_id, consumer_address, publisher_account.address, self._keeper)
        publisher_ether_balance = self._keeper.get_ether_balance(publisher_account.address)
        logger.debug(
            f'Agreement parameters:'
            f'\n  agreement id: {agreement_id}'
            f'\n  consumer address: {consumer_address}'
            f'\n  publisher address: {publisher_account.address}'
            f'\n  conditions ids: {condition_ids}'
            f'\n  asset did: {asset.did}'
            f'\n  agreement signature: {agreement_signature}'
            f'\n  agreement hash: {agreement_hash}'
            f'\n  EscrowAccessSecretStoreTemplate: '
            f'{self._keeper.access_template.address}'
            f'\n  publisher ether balance: {publisher_ether_balance}'
        )

    def _verify_service_agreement_signature(self, did, agreement_id, service_index,
                                            consumer_address, signature, ddo=None):
        """
        Verify service agreement signature.

        Verify that the given signature is truly signed by the `consumer_address`
        and represents this did's service agreement..

        :param did: DID, str
        :param agreement_id: id of the agreement, hex str
        :param service_index: identifier of the service inside the asset DDO, str
        :param consumer_address: ethereum account address of consumer, hex str
        :param signature: Signature, str
        :param ddo: DDO instance
        :return: True if signature is legitimate, False otherwise
        :raises: ValueError if service is not found in the ddo
        :raises: AssertionError if conditions keys do not match the on-chain conditions keys
        """
        if not ddo:
            ddo = self._asset_resolver.resolve(did)

        service_agreement = ddo.get_service_by_index(service_index)
        agreement_hash = service_agreement.get_service_agreement_hash(
            agreement_id, ddo.asset_id, consumer_address,
            Web3Provider.get_web3().toChecksumAddress(ddo.proof['creator']), self._keeper)

        recovered_address = self._keeper.personal_ec_recover(agreement_hash, signature)
        is_valid = (recovered_address == consumer_address)
        if not is_valid:
            logger.warning(f'Agreement signature failed: agreement hash is {agreement_hash.hex()}')

        return is_valid

    def _approve_token_transfer(self, amount, consumer_account):
        if self._keeper.token.get_token_balance(consumer_account.address) < amount:
            raise ValueError(
                f'Account {consumer_account.address} does not have sufficient tokens '
                f'to approve for transfer.')

        self._keeper.token.token_approve(self._keeper.payment_conditions.address, amount,
                                         consumer_account)

    def _get_agreement(self, agreement_id):
        """
        Retrieve the agreement data of agreement_id.

        :param agreement_id: id of the agreement, hex str
        :return: AgreementValues instance -- a namedtuple with the following attributes:

            did,
            owner,
            template_id,
            condition_ids,
            updated_by,
            block_number_updated

        """
        return self._keeper.agreement_manager.get_agreement(agreement_id)
