import os

import pytest
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceAuthorizationTypes, ServiceTypes
from common_utils_py.ddo.ddo import DDO
from contracts_lib_py.web3_provider import Web3Provider

from examples import ExampleConfig
from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.nevermined.agreements import check_token_address
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import (get_consumer_account, get_publisher_account,
                                              get_registered_ddo, get_registered_with_psk, log_event)


def test_buy_asset(publisher_instance_no_init, consumer_instance_no_init):
    config = ExampleConfig.get_config()
    keeper = Keeper.get_instance()
    # :TODO: enable the actual SecretStore
    # SecretStoreProvider.set_secret_store_class(SecretStore)
    pub_acc = get_publisher_account()

    # Register ddo
    ddo = get_registered_ddo(publisher_instance_no_init, pub_acc)
    assert isinstance(ddo, DDO)
    # nevermined here will be used only to publish the asset. Handling the asset by the publisher
    # will be performed by the Gateway server running locally

    # restore the http client because we want the actual Gateway server to do the work
    # not the GatewayMock.
    # Gateway.set_http_client(requests)
    consumer_account = get_consumer_account()

    downloads_path_elements = len(
        os.listdir(consumer_instance_no_init._config.downloads_path)) if os.path.exists(
        consumer_instance_no_init._config.downloads_path) else 0
    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    # This will send the access request to Gateway which in turn will execute the agreement on-chain
    consumer_instance_no_init.accounts.request_tokens(consumer_account, 100)

    agreement_id = consumer_instance_no_init.assets.order(
        ddo.did, sa.index, consumer_account, consumer_account)

    event_wait_time = 10
    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        event_wait_time,
        log_event(keeper.lock_payment_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'

    # give access
    publisher_instance_no_init.agreements.conditions.grant_access(
        agreement_id, ddo.asset_id, consumer_account.address, pub_acc)
    event = keeper.access_condition.subscribe_condition_fulfilled(
        agreement_id,
        event_wait_time,
        log_event(keeper.access_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessCondition.Fulfilled'
    assert consumer_instance_no_init.agreements.is_access_granted(agreement_id, ddo.did, consumer_account.address)

    amounts = list(map(int, service.get_param_value_by_name('_amounts')))
    receivers = service.get_param_value_by_name('_receivers')
    token_address = check_token_address(
        keeper, service.get_param_value_by_name('_tokenAddress'))

    publisher_instance_no_init.agreements.conditions.release_reward(
        agreement_id, ddo.asset_id, amounts, receivers, token_address, pub_acc)

    assert consumer_instance_no_init.assets.access(
        agreement_id,
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path)

    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

    # Check that we can access only an specific file in passing the index.
    assert consumer_instance_no_init.assets.access(
        agreement_id,
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path,
        1
    )
    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

    with pytest.raises(AssertionError):
        consumer_instance_no_init.assets.access(
            agreement_id,
            ddo.did,
            sa.index,
            consumer_account,
            config.downloads_path,
            -2
        )

    with pytest.raises(AssertionError):
        consumer_instance_no_init.assets.access(
            agreement_id,
            ddo.did,
            sa.index,
            consumer_account,
            config.downloads_path,
            3
        )

    # decrypt the contentUrls using the publisher account instead of consumer account.
    # if the secret store is working and ACL check is enabled, this should fail
    # since SecretStore decrypt will fail the checkPermissions check and the gateway will return
    # an http error code back
    with pytest.raises(ValueError) as e:
        consumer_instance_no_init.assets.access(
            agreement_id,
            ddo.did,
            sa.index,
            pub_acc,
            config.downloads_path
        )
        print(e)


@pytest.mark.skip(reason="Run in local with the gateway up")
def test_buy_asset_no_secret_store(publisher_instance_gateway, consumer_instance_gateway):
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    keeper = Keeper.get_instance()

    w3 = Web3Provider.get_web3()
    pub_acc = get_publisher_account()

    for method in [ServiceAuthorizationTypes.PSK_ECDSA, ServiceAuthorizationTypes.PSK_RSA]:
        # Register ddo
        ddo = get_registered_with_psk(publisher_instance_gateway, pub_acc, auth_method=method)
        assert isinstance(ddo, DDO)
        # nevermined here will be used only to publish the asset. Handling the asset by the publisher
        # will be performed by the Gateway server running locally

        # restore the http client because we want the actual Gateway server to do the work
        # not the GatewayMock.
        # Gateway.set_http_client(requests)
        consumer_account = get_consumer_account()

        downloads_path_elements = len(
            os.listdir(consumer_instance_gateway._config.downloads_path)) if os.path.exists(
            consumer_instance_gateway._config.downloads_path) else 0
        # sign agreement using the registered asset did above
        service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
        sa = ServiceAgreement.from_service_dict(service.as_dictionary())
        # This will send the access request to Gateway which in turn will execute the agreement on-chain
        consumer_instance_gateway.accounts.request_tokens(consumer_account, 100)
        agreement_id = consumer_instance_gateway.assets.order(
            ddo.did, sa.index, consumer_account, consumer_account)

        event_wait_time = 10
        event = keeper.access_template.subscribe_agreement_created(
            agreement_id,
            event_wait_time,
            log_event(keeper.access_template.AGREEMENT_CREATED_EVENT),
            (),
            wait=True
        )
        assert event, 'no event for EscrowAccessSecretStoreTemplate.AgreementCreated'

        event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
            agreement_id,
            event_wait_time,
            log_event(keeper.lock_payment_condition.FULFILLED_EVENT),
            (),
            wait=True
        )
        assert event, 'no event for LockRewardCondition.Fulfilled'

        # give access
        publisher_instance_gateway.agreements.conditions.grant_access(
            agreement_id, ddo.asset_id, consumer_account.address, pub_acc)
        event = keeper.access_condition.subscribe_condition_fulfilled(
            agreement_id,
            event_wait_time,
            log_event(keeper.access_condition.FULFILLED_EVENT),
            (),
            wait=True
        )
        assert event, 'no event for AccessSecretStoreCondition.Fulfilled'
        assert consumer_instance_gateway.agreements.is_access_granted(agreement_id, ddo.did, consumer_account.address)

        token_address = check_token_address(
            keeper, sa.get_param_value_by_name('_tokenAddress'))

        publisher_instance_gateway.agreements.conditions.release_reward(
            agreement_id, ddo.asset_id, sa.get_amounts_int(), sa.get_receivers(), token_address, pub_acc)

        assert consumer_instance_gateway.assets.access(
            agreement_id,
            ddo.did,
            sa.index,
            consumer_account,
            config.downloads_path)

        assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

        with pytest.raises(AssertionError):
            consumer_instance_gateway.assets.access(
                agreement_id,
                ddo.did,
                sa.index,
                consumer_account,
                config.downloads_path,
                -2
            )

        with pytest.raises(AssertionError):
            consumer_instance_gateway.assets.access(
                agreement_id,
                ddo.did,
                sa.index,
                consumer_account,
                config.downloads_path,
                3
            )
