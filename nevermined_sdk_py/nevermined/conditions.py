from common_utils_py.did import did_to_id
from common_utils_py.utils.utilities import to_checksum_addresses
from eth_utils import add_0x_prefix


class Conditions:
    """Nevermined conditions class."""

    def __init__(self, keeper):
        self._keeper = keeper

    def lock_payment(self, agreement_id, asset_id, amounts, receivers, token_address, account):
        """
        Lock reward condition.

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset identifier, str
        :param amounts: Amount of tokens, str[]
        :param receivers: Tokens receivers, str[]
        :param token_address: ERC20 token address or 0x0 if ETH
        :param account: Account
        :return: bool
        """
        total_price = 0
        for amount in amounts:
            total_price = total_price + int(amount)
        self._keeper.token.token_approve(self._keeper.lock_payment_condition.address, total_price,
                                         account)

        tx_hash = self._keeper.lock_payment_condition.fulfill(
            agreement_id,
            asset_id,
            self._keeper.escrow_payment_condition.address,
            token_address,
            amounts,
            to_checksum_addresses(receivers),
            account)

        receipt = self._keeper.lock_payment_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def grant_access(self, agreement_id, asset_id, grantee_address, account):
        """
        Grant access condition.

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset id, str
        :param grantee_address: Address, hex str
        :param account: Account
        :return:
        """
        tx_hash = self._keeper.access_condition.fulfill(
            agreement_id, asset_id, grantee_address, account
        )
        receipt = self._keeper.access_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def release_reward(self, agreement_id, asset_id, amounts, receivers, token_address, account):
        """
        Release reward condition.

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset id, str
        :param amounts: Amounts of tokens, int[]
        :param receivers: Token receivers, str[]
        :param token_address: ERC20 address or 0x0 if ETH payment
        :param account sending the transaction
        :return:
        """
        agreement_values = self._keeper.agreement_manager.get_agreement(agreement_id)
        consumer, provider = self._keeper.access_template.get_agreement_data(
            agreement_id)
        owner = agreement_values.owner
        access_id, lock_id = agreement_values.condition_ids[:2]
        tx_hash = self._keeper.escrow_payment_condition.fulfill(
            agreement_id,
            asset_id,
            amounts,
            to_checksum_addresses(receivers),
            self._keeper.escrow_payment_condition.address,
            token_address,
            lock_id,
            access_id,
            account
        )
        receipt = self._keeper.escrow_payment_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def refund_reward(self, agreement_id, asset_id, amounts, receivers, account):
        """
        Refund reward condition.

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset id, str
        :param amounts: Amounts of tokens, int[]
        :param receivers: Token receivers, str[]
        :param account sending the transaction
        :return:
        """
        return self.release_reward(agreement_id, asset_id, amounts, receivers, account)

    def show_nft(self, agreement_id, asset_id, holder_address, number_nfts, account):
        """
        Fulfill the NFT Holder condition demonstrating that holder_address has x number of nfts
        for a specific asset_id

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset id, str
        :param holder_address: Address, hex str
        :param number_nfts: int
        :param account: Account
        :return:
        """
        tx_hash = self._keeper.nft_holder_condition.fulfill(
            agreement_id, asset_id, holder_address, number_nfts, account
        )
        receipt = self._keeper.nft_access_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def grant_nft_access(self, agreement_id, asset_id, grantee_address, account):
        """
        Grant nft access condition.

        :param agreement_id: id of the agreement, hex str
        :param asset_id: asset id, str
        :param grantee_address: Address, hex str
        :param account: Account
        :return:
        """
        tx_hash = self._keeper.nft_access_condition.fulfill(
            agreement_id, asset_id, grantee_address, account
        )
        receipt = self._keeper.nft_access_condition.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)