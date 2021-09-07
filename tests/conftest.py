import uuid
from unittest.mock import Mock, MagicMock

import pytest
from common_utils_py.agreements.service_agreement import ServiceAgreement, ServiceAgreementTemplate
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.did import DID
from common_utils_py.metadata.metadata import Metadata
from common_utils_py.utils.utilities import generate_prefixed_id
from contracts_lib_py.contract_handler import ContractHandler
from contracts_lib_py.web3_provider import Web3Provider
from contracts_lib_py.web3.http_provider import CustomHTTPProvider
from web3 import Web3

from examples import ExampleConfig
from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from nevermined_sdk_py.assets.asset_executor import AssetExecutor
from nevermined_sdk_py.assets.asset_consumer import AssetConsumer
from nevermined_sdk_py.nevermined.agreements import Agreements
from tests.resources.helper_functions import (_get_asset, get_algorithm_ddo, get_consumer_account,
                                              get_consumer_instance, get_ddo_sample,
                                              get_metadata, get_publisher_account,
                                              get_publisher_instance, get_registered_ddo, get_workflow_ddo,
                                              setup_logging)
from tests.resources.mocks.secret_store_mock import SecretStoreMock

setup_logging()

ConfigProvider.set_config(ExampleConfig.get_config())


@pytest.fixture(autouse=True)
def setup_all():
    config = ExampleConfig.get_config()
    Web3Provider._web3 = Web3(CustomHTTPProvider(config.keeper_url))
    ContractHandler.artifacts_path = config.keeper_path
    Keeper.get_instance(artifacts_path=config.keeper_path)


@pytest.fixture
def metadata_provider_instance():
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    return Metadata(ConfigProvider.get_config().metadata_url)

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
    return get_consumer_instance(use_gateway_mock=False, use_ss_mock=False)


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
        'https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo1.json')
    asset._did = DID.encoded_did(asset.proof['checksum'])
    return asset

@pytest.fixture
def asset2():
    asset = _get_asset(
        'https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo2-update.json')
    asset._did = DID.encoded_did(asset.proof['checksum'])
    return  asset

@pytest.fixture
def ddo_sample():
    ddo = get_ddo_sample()
    ddo.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return ddo


@pytest.fixture
def ddo_algorithm():
    ddo = get_algorithm_ddo()
    ddo['service'][0]['attributes']['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return ddo


@pytest.fixture
def ddo_workflow():
    ddo = get_workflow_ddo()
    ddo['service'][0]['attributes']['main']['name'] = str(uuid.uuid4())
    return ddo


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return metadata


@pytest.fixture
def algorithm_ddo():
    ddo = get_algorithm_ddo()
    ddo['service'][0]['attributes']['main']['checksum'] = str(uuid.uuid4())
    return ddo


@pytest.fixture
def workflow_ddo():
    ddo = get_workflow_ddo()
    ddo['service'][0]['attributes']['main']['checksum'] = str(uuid.uuid4())
    return ddo


@pytest.fixture
def setup_agreements_environment(ddo_sample):
    consumer_acc = get_consumer_account()
    publisher_acc = get_publisher_account()
    keeper = Keeper.get_instance()

    ddo = ddo_sample
    did_seed = generate_prefixed_id()
    asset_id = keeper.did_registry.hash_did(did_seed, publisher_acc.address)
    ddo._did = DID.did(asset_id)

    keeper.did_registry.register(
        did_seed,
        checksum=Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
        url='localhost:5000',
        account=publisher_acc,
        providers=None
    )

    service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)
    agreement_id = ServiceAgreement.create_new_agreement_id()
    price = service_agreement.get_price()
    access_cond_id, lock_cond_id, escrow_cond_id = \
        service_agreement.generate_agreement_condition_ids(
            agreement_id, asset_id, consumer_acc.address, keeper
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


@pytest.fixture
def agreements():
    publisher_acc = get_publisher_account()
    keeper = Keeper.get_instance()
    w3 = Web3Provider.get_web3()
    did_resolver = Mock()
    ddo = get_ddo_sample()
    service = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    service.update_value(
        ServiceAgreementTemplate.TEMPLATE_ID_KEY,
        w3.toChecksumAddress(publisher_acc.address)
    )
    did_resolver.resolve = MagicMock(return_value=ddo)

    return Agreements(
        keeper,
        did_resolver,
        AssetConsumer,
        AssetExecutor,
        ConfigProvider.get_config()
    )
