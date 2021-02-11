from common_utils_py.did import did_to_id
from common_utils_py.utils.utilities import to_checksum_addresses
from eth_utils import add_0x_prefix


class Conditions:
    """Nevermined conditions class."""

    def __init__(self, keeper):
        self._keeper = keeper

    def lock_reward(self, agreement_id, amount, account):
        """
        Lock reward condition.

        :param agreement_id: id of the agreement, hex str
        :param amount: Amount of tokens, int
        :param account: Account
        :return: bool
        """
        self._keeper.token.token_approve(self._keeper.lock_reward_condition.address, amount,
                                         account)
        tx_hash = self._keeper.lock_reward_condition.fulfill(
            agreement_id, self._keeper.escrow_reward_condition.address, amount, account
        )
        receipt = self._keeper.lock_reward_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def grant_access(self, agreement_id, did, grantee_address, account):
        """
        Grant access condition.

        :param agreement_id: id of the agreement, hex str
        :param did: DID, str
        :param grantee_address: Address, hex str
        :param account: Account
        :return:
        """
        tx_hash = self._keeper.access_secret_store_condition.fulfill(
            agreement_id, add_0x_prefix(did_to_id(did)), grantee_address, account
        )
        receipt = self._keeper.access_secret_store_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def release_reward(self, agreement_id, amounts, receivers, account):
        """
        Release reward condition.

        :param agreement_id: id of the agreement, hex str
        :param amounts: Amounts of tokens, int[]
        :param receivers: Token receivers, str[]
        :param account sending the transaction
        :return:
        """
        agreement_values = self._keeper.agreement_manager.get_agreement(agreement_id)
        consumer, provider = self._keeper.escrow_access_secretstore_template.get_agreement_data(
            agreement_id)
        owner = agreement_values.owner
        access_id, lock_id = agreement_values.condition_ids[:2]
        tx_hash = self._keeper.escrow_reward_condition.fulfill(
            agreement_id,
            amounts,
            to_checksum_addresses(receivers),
            owner,
            lock_id,
            access_id,
            account
        )
        receipt = self._keeper.escrow_reward_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def refund_reward(self, agreement_id, amounts, receivers, account):
        """
        Refund reaward condition.

        :param agreement_id: id of the agreement, hex str
        :param amounts: Amounts of tokens, int[]
        :param receivers: Token receivers, str[]
        :param account sending the transaction
        :return:
        """
        return self.release_reward(agreement_id, amounts, receivers, account)
