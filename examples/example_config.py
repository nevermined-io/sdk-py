import logging
import os
import sys

from nevermined_sdk_py import Config


def get_variable_value(variable):
    if os.getenv(variable) is None:
        logging.error(f'you should provide a {variable}')
        sys.exit(1)
    else:
        return os.getenv(variable)


class ExampleConfig:
    SPREE = {
        "keeper-contracts": {
            "keeper.url": "http://172.17.0.1:8545",
            "keeper.path": "artifacts",
            "secret_store.url": "http://172.17.0.1:12001",
        },
        "resources": {
            "metadata.url": "http://172.17.0.1:5000",
            "gateway.url": "http://172.17.0.1:8030",
            "storage.path": "sdk.db",
            "downloads.path": "access-downloads"
        }
    }
    MUMBAI = {
        "keeper-contracts": {
            "keeper.url": "https://matic-mumbai.chainstacklabs.com",
        },
        "resources": {
            "metadata.url": "https://metadata.mumbai.nevermined.rocks/",
            "gateway.url": "https://gateway.mumbai.nevermined.rocks/",
            "downloads.path": "access-downloads"
        }
    }

    @staticmethod
    def get_config_net():
        return os.environ.get('TEST_NET', 'spree')

    @staticmethod
    def get_config():
        environment = ExampleConfig.get_config_net()
        logging.debug("Configuration loaded for environment '%s'", environment)

        if environment == 'spree':
            return Config(options_dict=ExampleConfig.SPREE)
        elif environment == 'mumbai':
            return Config(options_dict=ExampleConfig.MUMBAI)

        raise ValueError(f'No settings found for environment {environment}')