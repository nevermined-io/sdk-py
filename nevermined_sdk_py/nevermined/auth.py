import logging
from datetime import datetime

from contracts_lib_py.utils import add_ethereum_prefix_and_hash_msg
from contracts_lib_py.web3_provider import Web3Provider

from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.data_store.auth_tokens import AuthTokensStorage


class Auth:
    """Nevermined auth class.
    Provide basic management of a user auth token. This token can be used to emulate
    sign-in behaviour. The token can be stored and associated with an expiry time.
    This is useful in front-end applications that interact with a 3rd-party wallet
    apps. The advantage of using the auth token is to reduce the number of confirmation
    prompts requiring user action.

    The auth token works with a provider service such as Gateway which also uses this
    ocean module to handle auth tokens.

    Token format is "signature-timestamp".

    """
    DEFAULT_EXPIRATION_TIME = 30 * 24 * 60 * 60  # in seconds
    DEFAULT_MESSAGE = "Nevermined Protocol Authentication"

    def __init__(self, keeper, storage_path):
        self._keeper = keeper
        self._tokens_storage = AuthTokensStorage(storage_path)

    @staticmethod
    def _get_timestamp():
        return int(datetime.now().timestamp())

    def _get_expiration(self):
        return int(ConfigProvider.get_config().auth_token_expiration
                   or self.DEFAULT_EXPIRATION_TIME)

    def _get_raw_message(self):
        return ConfigProvider.get_config().auth_token_message or self.DEFAULT_MESSAGE

    def _get_message(self, timestamp):
        return f'{self._get_raw_message()}\n{timestamp}'

    def _get_message_and_time(self):
        timestamp = self._get_timestamp()
        return self._get_message(timestamp), timestamp

    @staticmethod
    def is_token_valid(token):
        return isinstance(token, str) and token.startswith('0x') and len(token.split('-')) == 2

    def get(self, account):
        """
        :param account: Account instance signing the token
        :return: hex str the token generated/signed by account
        """
        _message, _time = self._get_message_and_time()
        msg_hash = Web3Provider.get_web3().keccak(text=_message)
        try:
            prefixed_msg_hash = self._keeper.sign_hash(
                add_ethereum_prefix_and_hash_msg(msg_hash), account)
            return f'{prefixed_msg_hash}-{_time}'
        except Exception as e:
            logging.error(f'Error signing token: {str(e)}')

    def check(self, token):
        """
        :param token: hex str consist of signature and timestamp
        :return: hex str ethereum address
        """
        parts = token.split('-')
        if len(parts) < 2:
            return '0x0'

        sig, timestamp = parts
        if self._get_timestamp() > (int(timestamp) + self._get_expiration()):
            return '0x0'

        message = self._get_message(timestamp)
        address = self._keeper.personal_ec_recover(Web3Provider.get_web3().keccak(text=message), sig)
        return Web3Provider.get_web3().toChecksumAddress(address)

    def store(self, account):
        """
        :param account: Account instance signing the token
        :return:
            token that was generated and stored for this account
        """
        token = self.get(account)
        timestamp = token.split('-')[1]
        self._tokens_storage.write_token(account.address, token, timestamp)
        return token

    def restore(self, account):
        """
        :param account: Account instance to fetch the saved token
        :return:
            hex str the token retreived from storage
            None if no token found for this account
        """
        token = self._tokens_storage.read_token(account.address)[0]
        if not token:
            return None

        address = self.check(token)

        return token if address == account.address else None

    def is_stored(self, account):
        """
        :param account: Account instance
        :return: bool whether this account has a stored token
        """
        return self.restore(account) is not None
