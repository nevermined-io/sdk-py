import os

import pytest
from contracts_lib_py.web3_provider import Web3Provider
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.ddo.ddo import DDO
from secret_store_client.client import RPCError

from examples import ExampleConfig
from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import (get_consumer_account, get_publisher_account,
                                              get_registered_ddo, log_event)


def test_buy_asset(consumer_instance, publisher_instance):
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    keeper = Keeper.get_instance()
    # :TODO: enable the actual SecretStore
    # SecretStoreProvider.set_secret_store_class(SecretStore)
    w3 = Web3Provider.get_web3()
    pub_acc = get_publisher_account()

    # Register ddo
    ddo = get_registered_ddo(publisher_instance, pub_acc)
    assert isinstance(ddo, DDO)
    # nevermined here will be used only to publish the asset. Handling the asset by the publisher
    # will be performed by the Gateway server running locally

    # restore the http client because we want the actual Gateway server to do the work
    # not the GatewayMock.
    # Gateway.set_http_client(requests)
    consumer_account = get_consumer_account()

    downloads_path_elements = len(
        os.listdir(consumer_instance._config.downloads_path)) if os.path.exists(
        consumer_instance._config.downloads_path) else 0
    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    # This will send the consume request to Gateway which in turn will execute the agreement on-chain
    consumer_instance.accounts.request_tokens(consumer_account, 100)
    agreement_id = consumer_instance.assets.order(
        ddo.did, sa.index, consumer_account, auto_consume=False)

    event_wait_time = 10
    event = keeper.escrow_access_secretstore_template.subscribe_agreement_created(
        agreement_id,
        event_wait_time,
        log_event(keeper.escrow_access_secretstore_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowAccessSecretStoreTemplate.AgreementCreated'

    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        event_wait_time,
        log_event(keeper.lock_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'

    # give access
    publisher_instance.agreements.conditions.grant_access(
        agreement_id, ddo.did, consumer_account.address, pub_acc)
    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agreement_id,
        event_wait_time,
        log_event(keeper.access_secret_store_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessSecretStoreCondition.Fulfilled'
    assert consumer_instance.agreements.is_access_granted(agreement_id, ddo.did, consumer_account.address)

    publisher_instance.agreements.conditions.release_reward(
        agreement_id, sa.get_price(), pub_acc)

    assert consumer_instance.assets.consume(
        agreement_id,
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path)

    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

    # Check that we can consume only an specific file in passing the index.
    assert consumer_instance.assets.consume(
        agreement_id,
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path,
        2
    )
    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

    with pytest.raises(AssertionError):
        consumer_instance.assets.consume(
            agreement_id,
            ddo.did,
            sa.index,
            consumer_account,
            config.downloads_path,
            -2
        )

    with pytest.raises(AssertionError):
        consumer_instance.assets.consume(
            agreement_id,
            ddo.did,
            sa.index,
            consumer_account,
            config.downloads_path,
            3
        )

    # decrypt the contentUrls using the publisher account instead of consumer account.
    # if the secret store is working and ACL check is enabled, this should fail
    # since SecretStore decrypt will fail the checkPermissions check
    try:
        consumer_instance.assets.consume(
            agreement_id,
            ddo.did,
            sa.index,
            pub_acc,
            config.downloads_path
        )
    except RPCError:
        print('hooray, secret store is working as expected.')

    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        event_wait_time,
        log_event(keeper.escrow_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'

    assert w3.toHex(event.args['_agreementId']) == agreement_id
