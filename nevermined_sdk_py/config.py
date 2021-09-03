import configparser
import logging
import os
import site
from pathlib import Path

import nevermined_contracts

DEFAULT_KEEPER_HOST = 'localhost'
DEFAULT_KEEPER_PORT = 8545
DEFAULT_KEEPER_URL = 'http://localhost:8545'
DEFAULT_KEEPER_PATH = nevermined_contracts.get_artifacts_path()
DEFAULT_GAS_LIMIT = 4000000
DEFAULT_NAME_METADATA_URL = 'http://localhost:5000'
DEFAULT_NAME_GATEWAY_URL = 'http://localhost:8030'
DEFAULT_STORAGE_PATH = 'sdk.db'

NAME_KEEPER_URL = 'keeper.url'
NAME_KEEPER_PATH = 'keeper.path'
NAME_GAS_LIMIT = 'gas_limit'
NAME_METADATA_URL = 'metadata.url'
NAME_GATEWAY_URL = 'gateway.url'
NAME_STORAGE_PATH = 'storage.path'
NAME_AUTH_TOKEN_MESSAGE = 'auth_token_message'
NAME_AUTH_TOKEN_EXPIRATION = 'auth_token_expiration'

NAME_SECRET_STORE_URL = 'secret_store.url'
NAME_PARITY_URL = 'parity.url'
NAME_PARITY_ADDRESS = 'parity.address'
NAME_PARITY_PASSWORD = 'parity.password'

environ_names = {
    NAME_KEEPER_URL: ['KEEPER_URL', 'Keeper URL'],
    NAME_KEEPER_PATH: ['KEEPER_PATH', 'Path to the keeper contracts'],
    NAME_GAS_LIMIT: ['GAS_LIMIT', 'Gas limit'],
    NAME_METADATA_URL: ['METADATA_URL', 'Metadata URL'],
    NAME_GATEWAY_URL: ['GATEWAY_URL', 'Gateway URL'],
    NAME_STORAGE_PATH: ['STORAGE_PATH', 'Path to the local database file'],
    NAME_AUTH_TOKEN_MESSAGE: ['AUTH_TOKEN_MESSAGE',
                              'Message to use for generating user auth token'],
    NAME_AUTH_TOKEN_EXPIRATION: ['AUTH_TOKEN_EXPIRATION',
                                 'Auth token expiration time expressed in seconds'],
    NAME_SECRET_STORE_URL: ['SECRET_STORE_URL', 'Secret Store URL'],
    NAME_PARITY_URL: ['PARITY_URL', 'Parity URL'],
    NAME_PARITY_ADDRESS: ['PARITY_ADDRESS', 'Parity address'],
    NAME_PARITY_PASSWORD: ['PARITY_PASSWORD', 'Parity password'],
}

config_defaults = {
    'keeper-contracts': {
        NAME_KEEPER_URL: DEFAULT_KEEPER_URL,
        NAME_KEEPER_PATH: DEFAULT_KEEPER_PATH,
        NAME_GAS_LIMIT: DEFAULT_GAS_LIMIT,
        NAME_SECRET_STORE_URL: '',
        NAME_PARITY_URL: '',
        NAME_PARITY_ADDRESS: '',
        NAME_PARITY_PASSWORD: '',
    },
    'resources': {
        NAME_METADATA_URL: DEFAULT_NAME_METADATA_URL,
        NAME_GATEWAY_URL: DEFAULT_NAME_GATEWAY_URL,
        NAME_STORAGE_PATH: DEFAULT_STORAGE_PATH,
        NAME_AUTH_TOKEN_MESSAGE: '',
        NAME_AUTH_TOKEN_EXPIRATION: ''
    }
}


class Config(configparser.ConfigParser):
    """Class to manage the nevermined-sdk-py configuration."""

    def __init__(self, filename=None, options_dict=None, **kwargs):
        """
        Initialize Config class.

        Options available:

        [keeper-contracts]
        keeper.url = http://localhost:8545                            # Keeper-contracts url.
        keeper.path = artifacts                                       # Path of json abis.
        secret_store.url = http://localhost:12001                     # Secret store url.
        parity.url = http://localhost:8545                            # Parity client url.
        parity.address = 0x00bd138abd70e2f00903268f3db08f2d25677c9e   # Partity account address.
        parity.password = node0                                       # Parity account password.
        [resources]
        metadata.url = http://localhost:5000                          # Metadata url.
        gateway.url = http://localhost:8030                           # Gateway url.
        storage.path = sdk.db                                    # Path of sla back-up storage.

        :param filename: Path of the config file, str.
        :param options_dict: Python dict with the config, dict.
        :param kwargs: Additional args. If you pass text, you have to pass the plain text
        configuration.
        """
        configparser.ConfigParser.__init__(self)

        self.read_dict(config_defaults)
        self._web3_provider = None
        self._section_name = 'keeper-contracts'
        self._logger = logging.getLogger('config')

        if filename:
            self._logger.debug(f'Config: loading config file {filename}')
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        else:
            if 'text' in kwargs:
                self.read_string(kwargs['text'])

        if options_dict:
            self._logger.debug(f'Config: loading from dict {options_dict}')
            self.read_dict(options_dict)

        self._load_environ()

    def _load_environ(self):
        for option_name, environ_item in environ_names.items():
            value = os.environ.get(environ_item[0])
            if value is not None:
                self._logger.debug(f'Config: setting environ {option_name} = {value}')
                self.set(self._section_name, option_name, value)

    @property
    def keeper_path(self):
        """Path where the keeper-contracts artifacts are allocated."""
        keeper_path_string = self.get(self._section_name, NAME_KEEPER_PATH)
        path = Path(keeper_path_string).expanduser().resolve()

        if os.path.exists(path):
            pass
        elif os.getenv('VIRTUAL_ENV'):
            path = os.path.join(os.getenv('VIRTUAL_ENV'), 'artifacts')
        else:
            path = os.path.join(site.PREFIXES[0], 'artifacts')
        return path

    @property
    def storage_path(self):
        """Path to save the current execution of the service agreements and restart if needed."""
        return self.get('resources', NAME_STORAGE_PATH)

    @property
    def keeper_url(self):
        """URL of the keeper. (e.g.): http://mykeeper:8545."""
        return self.get(self._section_name, NAME_KEEPER_URL)

    @property
    def gas_limit(self):
        """Ethereum gas limit."""
        return int(self.get(self._section_name, NAME_GAS_LIMIT))

    @property
    def metadata_url(self):
        """URL of metadata component. (e.g.): http://mymetadata:5000."""
        return self.get('resources', NAME_METADATA_URL)

    @property
    def gateway_url(self):
        """URL of gateway component. (e.g.): http://mygateway:8030."""
        return self.get('resources', NAME_GATEWAY_URL)

    @property
    def secret_store_url(self):
        """URL of the secret store component. (e.g.): http://mysecretstore:12001."""
        return self.get(self._section_name, NAME_SECRET_STORE_URL)

    @property
    def parity_url(self):
        """URL of parity client. (e.g.): http://myparity:8545."""
        return self.get(self._section_name, NAME_PARITY_URL)

    @property
    def parity_address(self):
        """Parity address. (e.g.): 0x00bd138abd70e2f00903268f3db08f2d25677c9e."""
        return self.get(self._section_name, NAME_PARITY_ADDRESS)

    @property
    def parity_password(self):
        """Parity password for your address. (e.g.): Mypass."""
        return self.get(self._section_name, NAME_PARITY_PASSWORD)

    @property
    def downloads_path(self):
        """Path for the downloads of assets."""
        return self.get('resources', 'downloads.path')

    @property
    def auth_token_message(self):
        return self.get('resources', NAME_AUTH_TOKEN_MESSAGE)

    @property
    def auth_token_expiration(self):
        return self.get('resources', NAME_AUTH_TOKEN_EXPIRATION)

    @property
    def web3_provider(self):
        """Web3 provider"""
        return self._web3_provider

    @web3_provider.setter
    def web3_provider(self, web3_provider):
        self._web3_provider = web3_provider
