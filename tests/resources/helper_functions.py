import json
import logging
import logging.config
import os
import pathlib
import uuid
from urllib.request import urlopen

import coloredlogs
import yaml
from common_utils_py.ddo.ddo import DDO
from contracts_lib_py.utils import get_account

from nevermind_sdk_py.gateway.gateway_provider import GatewayProvider
from nevermind_sdk_py.nevermind.keeper import NevermindKeeper as Keeper
from nevermind_sdk_py.nevermind.nevermind import Nevermind
from nevermind_sdk_py.secret_store.secret_store_provider import SecretStoreProvider
from tests.resources.mocks.gateway_mock import GatewayMock
from tests.resources.mocks.secret_store_mock import SecretStoreMock

PUBLISHER_INDEX = 1
CONSUMER_INDEX = 0


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def init_ocn_tokens(nevermind, account, amount=100):
    nevermind.accounts.request_tokens(account, amount)
    Keeper.get_instance().token.token_approve(
        Keeper.get_instance().dispenser.address,
        amount,
        account
    )


def get_publisher_account():
    return get_account(0)


def get_consumer_account():
    return get_account(1)


def get_publisher_instance(init_tokens=True, use_ss_mock=True, use_gateway_mock=True):
    nevermind = Nevermind()
    account = get_publisher_account()
    nevermind.main_account = account
    if init_tokens:
        init_ocn_tokens(nevermind, nevermind.main_account)
    if use_ss_mock:
        SecretStoreProvider.set_secret_store_class(SecretStoreMock)
    if use_gateway_mock:
        GatewayProvider.set_gateway_class(GatewayMock)

    return nevermind


def get_consumer_instance(init_tokens=True, use_ss_mock=True, use_gateway_mock=True):
    nevermind = Nevermind()
    account = get_consumer_account()
    nevermind.main_account = account
    if init_tokens:
        init_ocn_tokens(nevermind, nevermind.main_account)
    if use_ss_mock:
        SecretStoreProvider.set_secret_store_class(SecretStoreMock)
    if use_gateway_mock:
        GatewayProvider.set_gateway_class(GatewayMock)

    return nevermind


def _get_asset(url):
    return DDO(json_text=get_assset_json_text(url))


def get_assset_json_text(url):
    return json.dumps(json.loads(urlopen(url).read().decode('utf-8')))


def get_ddo_sample():
    return _get_asset(
        "https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs"
        "/examples/metadata/v0.1/ddo-example-access.json")


def get_algorithm_ddo():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs"
        "/examples/metadata/v0.1/ddo-example-algorithm.json").read().decode(
        'utf-8'))


def get_workflow_ddo():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs"
        "/examples/metadata/v0.1/ddo-example-workflow.json").read().decode(
        'utf-8'))


def get_computing_metadata():
    return json.loads(urlopen(
        'https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs'
        '/examples/metadata/v0.1/computing-metadata.json').read().decode(
        'utf-8'))


def get_computing_ddo():
    return _get_asset(
        "https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs"
        "/examples/compute/v0.1/ddo.computing.json")


def get_registered_ddo(ocean_instance, account):
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = ocean_instance.assets.create(metadata, account)
    return ddo


def log_event(event_name):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')

    return _process_event


def get_metadata():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs"
        "/examples/metadata/v0.1/metadata1.json").read().decode(
        'utf-8'))


def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
    """Logging setup."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
                logging.info(f'Logging configuration loaded from file: {path}')
            except Exception as ex:
                print(ex)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
