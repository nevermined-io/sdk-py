import logging

from common_utils_py.http_requests.requests_session import get_requests_session
from contracts_lib_py.web3_provider import Web3Provider


logger = logging.getLogger(__name__)


class Faucet:
    """
    `Faucet`.

    The main functions available are:
    - Request eht for an account

    """
    _http_client = get_requests_session()

    @staticmethod
    def set_http_client(http_client):
        """Set the http client to something other than the default `requests`"""
        Faucet._http_client = http_client

    @staticmethod
    def get_faucet_url(config):
        """
        Return the Gateway component url.

        :param config: Config
        :return: Url, str
        """
        faucet_url = 'http://localhost:3001'
        if config.has_option('resources', 'faucet.url'):
            faucet_url = config.get('resources', 'faucet.url') or faucet_url

        faucet_path = '/faucet'
        return f'{faucet_url}{faucet_path}'

    @staticmethod
    def get_eth_from_faucet(config, address):
        payload = {'address': Web3Provider.get_web3().toChecksumAddress(address), 'agent': 'sdk-py'}
        response = Faucet._http_client.post(Faucet.get_faucet_url(config), data=payload, headers={'Accept': 'application/json'})

        if not response.ok:
            raise ValueError(response.text)

        return response

