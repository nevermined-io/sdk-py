import logging

from eth_utils import add_0x_prefix
from contracts_lib_py.utils import process_tx_receipt
from contracts_lib_py.web3_provider import Web3Provider
from common_utils_py.did import did_to_id
from common_utils_py.did_resolver.did_resolver import DIDResolver

from nevermined_sdk_py.gateway import GatewayProvider
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from nevermined_sdk_py.secret_store import SecretStoreProvider

logger = logging.getLogger(__name__)


def refund_reward(event, agreement_id, did, service_agreement, price, consumer_account,
                  publisher_address, condition_ids, escrow_condition_id):
    """
    Refund the reward to the publisher address.

    :param event: AttributeDict with the event data.
    :param agreement_id: id of the agreement, hex str
    :param did: DID, str
    :param service_agreement: ServiceAgreement instance
    :param price: Asset price, int
    :param consumer_account: Account instance of the consumer
    :param publisher_address: ethereum account address of publisher, hex str
    :param condition_ids: is a list of bytes32 content-addressed Condition IDs, bytes32
    :param escrow_condition_id: hex str the id of escrow reward condition at this `agreement_id`
    """
    logger.debug(f"trigger refund (agreement {agreement_id}) after event {event}.")
    if Keeper.get_instance().condition_manager.get_condition_state(escrow_condition_id) > 1:
        logger.debug(
            f'escrow payment condition already fulfilled/aborted: '
            f'agreementId={agreement_id}, escrow reward conditionId={escrow_condition_id},'
            f' publisher={publisher_address}'
        )
        return

    access_id, lock_id = condition_ids[:2]
    name_to_parameter = {param.name: param for param in
                         service_agreement.condition_by_name['escrowPayment'].parameters}
    document_id = add_0x_prefix(name_to_parameter['_documentId'].value)
    asset_id = add_0x_prefix(did_to_id(did))
    did_owner = Keeper.get_instance().agreement_manager.get_agreement_did_owner(agreement_id)
    assert document_id == asset_id, f'document_id {document_id} <=> asset_id {asset_id} mismatch.'
    assert price == service_agreement.get_price(), 'price mismatch.'
    try:
        escrow_condition = Keeper.get_instance().escrow_payment_condition
        tx_hash = escrow_condition.fulfill(
            agreement_id,
            price,
            Web3Provider.get_web3().toChecksumAddress(did_owner),
            consumer_account.address,
            lock_id,
            access_id,
            consumer_account
        )
        process_tx_receipt(
            tx_hash,
            getattr(escrow_condition.contract.events, escrow_condition.FULFILLED_EVENT)(),
            'EscrowReward.Fulfilled'
        )
    except Exception as e:
        logger.error(
            f'Error when doing escrow_payment_condition.fulfills (agreementId {agreement_id}): {e}',
            exc_info=1)
        raise e


def consume_asset(event, agreement_id, did, service_agreement, consumer_account, consume_callback,
                  secret_store_url, parity_url, downloads_path):
    """
    Consumption of an asset after get the event call.

    :param event: AttributeDict with the event data.
    :param agreement_id: id of the agreement, hex str
    :param did: DID, str
    :param service_agreement: ServiceAgreement instance
    :param consumer_account: Account instance of the consumer
    :param consume_callback:
    :param secret_store_url: str URL of secret store node for retrieving decryption keys
    :param parity_url: str URL of parity client to use for secret store encrypt/decrypt
    :param downloads_path: str path to save downloaded files
    """
    logger.debug(f"consuming asset (agreementId {agreement_id}) after event {event}.")
    if consume_callback:
        secret_store = SecretStoreProvider.get_secret_store(
            secret_store_url, parity_url, consumer_account
        )
        gateway = GatewayProvider.get_gateway()

        consume_callback(
            agreement_id,
            service_agreement.service_definition_id,
            DIDResolver(Keeper.get_instance().did_registry).resolve(did),
            consumer_account,
            downloads_path,
            gateway,
            secret_store
        )
