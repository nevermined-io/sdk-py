#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import uuid

import pytest
from contracts_lib_py.contract_handler import ContractHandler
from contracts_lib_py.web3_provider import Web3Provider
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.did import DID

from examples import ExampleConfig
from nevermind_sdk_py import ConfigProvider
from nevermind_sdk_py.ocean.keeper import SquidKeeper as Keeper
from tests.resources.helper_functions import (get_consumer_account, get_consumer_ocean_instance,
                                              get_ddo_sample, get_metadata, get_publisher_account,
                                              get_publisher_ocean_instance, get_registered_ddo,
                                              setup_logging)
from tests.resources.mocks.secret_store_mock import SecretStoreMock
from tests.resources.tiers import should_run_test

setup_logging()

if should_run_test('e2e'):
    ConfigProvider.set_config(ExampleConfig.get_config())


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
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def publisher_ocean_instance_brizo():
    return get_publisher_ocean_instance(use_brizo_mock=False)


@pytest.fixture
def consumer_ocean_instance_brizo():
    return get_consumer_ocean_instance(use_brizo_mock=False)


@pytest.fixture
def registered_ddo():
    return get_registered_ddo(get_publisher_ocean_instance(), get_publisher_account())


@pytest.fixture
def web3_instance():
    config = ExampleConfig.get_config()
    return Web3Provider.get_web3(config.keeper_url)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return metadata


@pytest.fixture
def setup_agreements_enviroment():
    consumer_acc = get_consumer_account()
    publisher_acc = get_publisher_account()
    keeper = Keeper.get_instance()

    ddo = get_ddo_sample()
    ddo._did = DID.did({'0': '0x987654321'})
    keeper.did_registry.register(
        ddo.asset_id,
        checksum=Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
        url='aquarius:5000',
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
