import uuid

import pytest
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.did import DID
from common_utils_py.metadata.metadata import Metadata
from contracts_lib_py.contract_handler import ContractHandler
from contracts_lib_py.web3_provider import Web3Provider

from examples import ExampleConfig
from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import (_get_asset, get_consumer_account,
                                              get_consumer_instance, get_ddo_sample,
                                              get_metadata, get_publisher_account,
                                              get_publisher_instance, get_registered_ddo,
                                              setup_logging)
from tests.resources.mocks.secret_store_mock import SecretStoreMock

setup_logging()

ConfigProvider.set_config(ExampleConfig.get_config())
metadata_provider = Metadata(ConfigProvider.get_config().metadata_url)


@pytest.fixture(autouse=True)
def setup_all():
    config = ExampleConfig.get_config()
    Web3Provider.get_web3(config.keeper_url)
    ContractHandler.artifacts_path = config.keeper_path
    Keeper.get_instance(artifacts_path=config.keeper_path)


@pytest.fixture
def secret_store():
    return SecretStoreMock


@pytest.fixture
def publisher_instance():
    return get_publisher_instance()


@pytest.fixture
def consumer_instance():
    return get_consumer_instance()


@pytest.fixture
def publisher_instance_no_init():
    return get_publisher_instance(False, False, False)


@pytest.fixture
def consumer_instance_no_init():
    return get_consumer_instance(False, False, False)


@pytest.fixture
def publisher_instance_gateway():
    return get_publisher_instance(use_gateway_mock=False, use_ss_mock=False)


@pytest.fixture
def consumer_instance_gateway():
    return get_consumer_instance(use_gateway_mock=False,  use_ss_mock=False)


@pytest.fixture
def registered_ddo():
    return get_registered_ddo(get_publisher_instance(), get_publisher_account())


@pytest.fixture
def web3_instance():
    config = ExampleConfig.get_config()
    return Web3Provider.get_web3(config.keeper_url)


@pytest.fixture
def asset1():
    asset = _get_asset(
        'https://raw.githubusercontent.com/keyko-io/nevermined-docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo1.json')
    asset._did = DID.did(asset.proof['checksum'])
    yield asset
    metadata_provider.retire_all_assets()


@pytest.fixture
def asset2():
    asset = _get_asset(
        'https://raw.githubusercontent.com/keyko-io/nevermined-docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo2-update.json')
    asset._did = DID.did(asset.proof['checksum'])
    return asset


@pytest.fixture
def ddo_sample():
    return get_ddo_sample()


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return metadata


@pytest.fixture
def setup_agreements_enviroment(ddo_sample):
    consumer_acc = get_consumer_account()
    publisher_acc = get_publisher_account()
    keeper = Keeper.get_instance()

    ddo = ddo_sample
    ddo._did = DID.did({'0': '0x987654321'})
    keeper.did_registry.register(
        ddo.asset_id,
        checksum=Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
        url='metadata:5000',
        account=publisher_acc,
        providers=None
    )

    registered_ddo = ddo
    asset_id = registered_ddo.asset_id
    service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)
    agreement_id = ServiceAgreement.create_new_agreement_id()
    price = service_agreement.get_price()
    access_cond_id, lock_cond_id, escrow_cond_id = \
        service_agreement.generate_agreement_condition_ids(
            agreement_id, asset_id, consumer_acc.address, publisher_acc.address, keeper
        )

    return (
        keeper,
        publisher_acc,
        consumer_acc,
        agreement_id,
        asset_id,
        price,
        service_agreement,
        (lock_cond_id, access_cond_id, escrow_cond_id),
    )
