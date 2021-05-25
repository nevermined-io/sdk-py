import logging
import logging
import os

from common_utils_py.did import did_to_id, convert_to_bytes

logger = logging.getLogger(__name__)


class NFTs:
    """Nevermined NFTs class."""

    def __init__(self, keeper):
        self._keeper = keeper

    def mint(self, did, amount, account):
        """
        Mint an amount of nfts.
        :param did: the id of an asset on-chain, hex str
        :param amount: amount of nft to be minted, int
        :param account: Account executing the action
        """
        return self._keeper.did_registry.mint(convert_to_bytes(did), amount, account)

    def burn(self, did, amount, account):
        """
        Burn an amount of nfts.
        :param did: the id of an asset on-chain, hex str
        :param amount: amount of nft to be burnt, int
        :param account: Account executing the action
        """
        return self._keeper.did_registry.burn(convert_to_bytes(did), amount, account)

    def transfer_nft(self, did, address, amount, account):
        """
        Transfer nft to another address. Return true if successful

        :param did: the id of an asset on-chain, hex str
        :param address: ethereum account address, hex str
        :param amount: amount of nft to be transfer, int
        :param account: Account executing the action

        """
        return self._keeper.did_registry.transfer_nft(did_to_id(did), address, amount, account)

    def balance(self, address, did):
        """
        Return nft balance.

        :param address: ethereum account address, hex str
        :param did: the id of an asset on-chain, hex str
        """
        return self._keeper.did_registry.balance(address, convert_to_bytes(did))


