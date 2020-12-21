from collections import namedtuple

from contracts_lib_py.account import Account

Balance = namedtuple('Balance', ('eth', 'ocn'))


class Accounts:
    """Nevermined accounts class."""

    def __init__(self, keeper, config, nevermined_tokens, faucet):
        self._keeper = keeper
        self._config = config
        self._nevermined_tokens = nevermined_tokens
        self._faucet = faucet
        self._accounts = [Account(account_address) for account_address in self._keeper.accounts]
        if config.parity_address and config.parity_password:
            address = config.parity_address.lower()
            for account in self._accounts:
                if account.address.lower() == address:
                    account.password = config.parity_password
                    break

    @property
    def _accounts_addresses(self):
        """
        Return a list with the account addresses.

        :return: list
        """
        return [a.address for a in self._accounts]

    def list(self):
        """
        Return list of Account instances available in the current ethereum node

        :return: list of Account instances
        """
        return self._accounts[:]

    def balance(self, account):
        """
        Return the balance, a tuple with the eth and nevermined balance.

        :param account: Account instance to return the balance of
        :return: Balance tuple of (eth, ocn)
        """
        return Balance(self._keeper.get_ether_balance(account.address),
                       self._keeper.token.get_token_balance(account.address))

    def request_tokens(self, account, amount):
        """
        Request an amount of ocean tokens for an account.

        :param account: Account instance making the tokens request
        :param amount: int amount of tokens requested
        :raises OceanInvalidTransaction: if transaction fails
        :return: bool
        """
        return self._nevermined_tokens.request(account, amount)

    def request_eth_from_faucet(self, address):
        """
        Requests Network ETH to the faucet for paying the transactions gas
        :param address: eth address requesting, hex str
        """
        return self._faucet.get_eth_from_faucet(self._config, address)
