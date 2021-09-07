from nevermined_sdk_py.config_provider import ConfigProvider
from examples.example_config import ExampleConfig
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
from common_utils_py.http_requests.requests_session import get_requests_session
from contracts_lib_py.utils import get_account
from common_utils_py.agreements.service_factory import ServiceDescriptor
from nevermined_sdk_py.gateway.gateway_provider import GatewayProvider
from nevermined_sdk_py.gateway.gateway import Gateway
from nevermined_sdk_py.secret_store.secret_store import SecretStore
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from nevermined_sdk_py.nevermined.nevermined import Nevermined
from nevermined_sdk_py.secret_store.secret_store_provider import SecretStoreProvider
from tests.resources.mocks.gateway_mock import GatewayMock
from tests.resources.mocks.secret_store_mock import SecretStoreMock
from common_utils_py.utils.utilities import to_checksum_addresses

PUBLISHER_INDEX = 1
CONSUMER_INDEX = 0


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def init_ocn_tokens(nevermined, account, amount=100):
    nevermined.accounts.request_tokens(account, amount)
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
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    nevermined = Nevermined()
    account = get_publisher_account()
    nevermined.main_account = account
    if init_tokens:
        init_ocn_tokens(nevermined, nevermined.main_account)
    if use_ss_mock:
        SecretStoreProvider.set_secret_store_class(SecretStoreMock)
    else:
        SecretStoreProvider.set_secret_store_class(SecretStore)
    if use_gateway_mock:
        GatewayProvider.set_gateway_class(GatewayMock)
    else:
        Gateway.set_http_client(get_requests_session())
        GatewayProvider.set_gateway_class(Gateway)

    return nevermined


def get_consumer_instance(init_tokens=True, use_ss_mock=True, use_gateway_mock=True):
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    nevermined = Nevermined()
    account = get_consumer_account()
    nevermined.main_account = account
    if init_tokens:
        init_ocn_tokens(nevermined, nevermined.main_account)
    if use_ss_mock:
        SecretStoreProvider.set_secret_store_class(SecretStoreMock)
    else:
        SecretStoreProvider.set_secret_store_class(SecretStore)
    if use_gateway_mock:
        GatewayProvider.set_gateway_class(GatewayMock)
    else:
        Gateway.set_http_client(get_requests_session())
        GatewayProvider.set_gateway_class(Gateway)

    return nevermined


def _get_asset(url):
    return DDO(json_text=get_assset_json_text(url))


def get_assset_json_text(url):
    return json.dumps(json.loads(urlopen(url).read().decode('utf-8')))


def get_ddo_sample():
    return _get_asset(
        "https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs/examples/metadata/v0.1/ddo-example-access.json")


def get_algorithm_ddo():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/nevermined-io/docs/1a853613bd9e9d633474e571d3225378a37b6451/docs/architecture/specs/examples/metadata/v0.1/ddo-example-algorithm.json").read().decode(
        'utf-8'))


def get_workflow_ddo():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs/examples/metadata/v0.1/ddo-example-workflow.json").read().decode(
        'utf-8'))


def get_computing_metadata():
    return json.loads(urlopen(
        'https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs/examples/metadata/v0.1/computing-metadata.json').read().decode(
        'utf-8'))


def get_sample_nft_ddo():
    return json.loads(urlopen(
        'https://raw.githubusercontent.com/keyko-io/nevermined-docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo_nft.json').read().decode(
        'utf-8'))


def get_computing_ddo():
    return _get_asset(
        "https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs/examples/compute/v0.1/ddo.computing.json")


def get_registered_ddo(nevermined_instance, account):
    metadata = get_metadata()
    asset_rewards = {
        "_amounts": ["10", "2"],
        "_receivers": ["0x00Bd138aBD70e2F00903268F3Db08f2D25677C9e", "0x068ed00cf0441e4829d9784fcbe7b9e26d4bd8d0"]
    }
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = nevermined_instance.assets.create(metadata, account, asset_rewards=asset_rewards)
    return ddo


def get_registered_ddo_nft(nevermined_instance, account):
    ddo = get_sample_nft_ddo()
    metadata = ddo['service'][0]['attributes']
    metadata['main']['files'][0][
        'url'] = "https://raw.githubusercontent.com/tbertinmahieux/MSongsDB/master/Tasks_Demos" \
                 "/CoverSongs/shs_dataset_test.txt?" + str(uuid.uuid4())
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())

    escrow_payment_condition = ddo['service'][1]['attributes']['serviceAgreementTemplate']['conditions'][2]
    _number_nfts = 1
    _amounts = get_param_value_by_name(escrow_payment_condition['parameters'], '_amounts')
    _receivers = to_checksum_addresses(
        get_param_value_by_name(escrow_payment_condition['parameters'], '_receivers'))

    transfer_nft_condition = ddo['service'][1]['attributes']['serviceAgreementTemplate']['conditions'][1]
    _nftHolder = get_param_value_by_name(transfer_nft_condition['parameters'], '_nftHolder')


    _total_price = 0
    for i in _amounts:
        _total_price += int(i)

    asset_rewards = {
        "_amounts": _amounts,
        "_receivers": _receivers
    }

    metadata['main']['price'] = _total_price

    access_service_attributes = {"main": {
        "name": "nftAccessAgreement",
        "creator": account.address,
        "timeout": 3600,
        "price": _total_price,
        "_amounts": _amounts,
        "_receivers": _receivers,
        "_numberNfts": str(_number_nfts),
        "datePublished": metadata['main']['dateCreated']
    }}

    sales_service_attributes = access_service_attributes
    sales_service_attributes['main']['name'] = 'nftSalesAgreement'
    sales_service_attributes['main']['_nftHolder'] = _nftHolder

    nft_sales_service_descriptor = ServiceDescriptor.nft_sales_service_descriptor(
        sales_service_attributes,
        'http://localhost:8030'
    )
    nft_access_service_descriptor = ServiceDescriptor.nft_access_service_descriptor(
        access_service_attributes,
        'http://localhost:8030'
    )
    ddo = nevermined_instance.assets.create(metadata, account,
                                            [nft_sales_service_descriptor, nft_access_service_descriptor],
                                            asset_rewards=asset_rewards,
                                            royalties= 0, cap=10, mint=10)
    return ddo


def get_registered_with_psk(nevermined_instance, account, auth_method):
    metadata = get_ddo_sample()
    ddo = nevermined_instance.assets.create(metadata.metadata, account,
                                            authorization_type=auth_method)
    return ddo


def log_event(event_name):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')

    return _process_event


def get_rsa_private_key_file():
    return os.getenv('RSA_PRIVKEY_FILE', '')


def get_rsa_public_key_file():
    return os.getenv('RSA_PUBKEY_FILE', '')


def get_metadata():
    return json.loads(urlopen(
        "https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs"
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


def get_param_value_by_name(parameters, name):
    """
    Return the value from the conditions parameters given the param name.

    :return: Object
    """
    for p in parameters:
        if p['name'] == name:
            return p['value']