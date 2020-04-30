import logging


class Tokens:
    """Nevermined token class."""

    def __init__(self, keeper):
        self._keeper = keeper

    def request(self, account, amount):
        """
        Request a number of tokens to be minted and transfered to `account`

        :param account: Account instance requesting the tokens
        :param amount: int number of tokens to request
        :return: bool
        """
        if not self._keeper.dispenser:
            network_id = self._keeper.get_network_id()
            logging.warning(f'The Dispenser contract is not available for the current '
                            f'keeper network {self._keeper.get_network_name(network_id)}.')
            return False

        return self._keeper.dispenser.request_tokens(amount, account)

    def transfer(self, receiver_address, amount, sender_account):
        """
        Transfer a number of tokens from `sender_account` to `receiver_address`

        :param receiver_address: hex str ethereum address to receive this transfer of tokens
        :param amount: int number of tokens to transfer
        :param sender_account: Account instance to take the tokens from
        :return: bool
        """
        self._keeper.token.transfer(receiver_address, amount, sender_account)
