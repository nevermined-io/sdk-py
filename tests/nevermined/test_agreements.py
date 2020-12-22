from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes, ServiceTypesIndices

from nevermined_sdk_py.gateway.gateway import Gateway
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import log_event
from tests.resources.mocks.gateway_mock import GatewayMock


def test_sign_agreement(publisher_instance, consumer_instance, registered_ddo):
    # point consumer_instance's Gateway mock to the publisher's nevermined instance
    Gateway.set_http_client(
        GatewayMock(publisher_instance, publisher_instance.main_account))

    consumer_acc = consumer_instance.main_account
    keeper = Keeper.get_instance()

    publisher_acc = publisher_instance.main_account

    did = registered_ddo.did
    asset_id = registered_ddo.asset_id
    ddo = consumer_instance.assets.resolve(did)
    service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)

    price = service_agreement.get_price()

    # Give consumer some tokens
    keeper.dispenser.request_vodkas(price * 2, consumer_acc)

    agreement_id, signature = consumer_instance.agreements.prepare(
        did, consumer_acc, ServiceTypesIndices.DEFAULT_ACCESS_INDEX)

    success = publisher_instance.agreements.create(
        did,
        ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
        agreement_id,
        consumer_acc.address,
        publisher_acc
    )
    assert success, 'createAgreement failed.'

    # Verify condition types (condition contracts)
    agreement_values = keeper.agreement_manager.get_agreement(agreement_id)
    assert agreement_values.did == asset_id, ''
    cond_types = keeper.escrow_access_secretstore_template.get_condition_types()
    for i, cond_id in enumerate(agreement_values.condition_ids):
        cond = keeper.condition_manager.get_condition(cond_id)
        assert cond.type_ref == cond_types[i]

    access_cond_id, lock_cond_id, escrow_cond_id = agreement_values.condition_ids

    # Fulfill lock_reward_condition is done automatically when create agreement is done correctly
    assert 2 == keeper.condition_manager.get_condition_state(lock_cond_id), ''
    assert 1 == keeper.condition_manager.get_condition_state(access_cond_id), ''
    assert 1 == keeper.condition_manager.get_condition_state(escrow_cond_id), ''

    # Fulfill access_secret_store_condition
    tx_hash = keeper.access_secret_store_condition.fulfill(
        agreement_id, asset_id, consumer_acc.address, publisher_acc
    )
    keeper.access_secret_store_condition.get_tx_receipt(tx_hash)
    assert 2 == keeper.condition_manager.get_condition_state(access_cond_id), ''
    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.access_secret_store_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessSecretStoreCondition.Fulfilled'

    # Fulfill escrow_reward_condition
    tx_hash = keeper.escrow_reward_condition.fulfill(
        agreement_id, price, publisher_acc.address,
        consumer_acc.address, lock_cond_id,
        access_cond_id, publisher_acc
    )
    keeper.escrow_reward_condition.get_tx_receipt(tx_hash)
    assert 2 == keeper.condition_manager.get_condition_state(escrow_cond_id), ''
    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    publisher_instance.assets.retire(did)


# @pytest.mark.skip(reason="Failing some times with actions")
def test_agreement_status(setup_agreements_enviroment, agreements):
    (
        keeper,
        publisher_acc,
        consumer_acc,
        agreement_id,
        asset_id,
        price,
        service_agreement,
        (lock_cond_id, access_cond_id, escrow_cond_id),

    ) = setup_agreements_enviroment

    success = keeper.escrow_access_secretstore_template.create_agreement(
        agreement_id,
        asset_id,
        [access_cond_id, lock_cond_id, escrow_cond_id],
        service_agreement.conditions_timelocks,
        service_agreement.conditions_timeouts,
        consumer_acc.address,
        publisher_acc
    )
    print('create agreement: ', success)
    assert success, f'createAgreement failed {success}'
    event = keeper.escrow_access_secretstore_template.subscribe_agreement_created(
        agreement_id,
        10,
        log_event(keeper.escrow_access_secretstore_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AgreementCreated '
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 1,
                                                              "accessSecretStore": 1,
                                                              "escrowReward": 1
                                                              }
                                               }

    agreements.conditions.lock_reward(agreement_id, price, consumer_acc)

    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.lock_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessSecretStore": 1,
                                                              "escrowReward": 1
                                                              }
                                               }
    tx_hash = keeper.access_secret_store_condition.fulfill(
        agreement_id, asset_id, consumer_acc.address, publisher_acc)
    keeper.access_secret_store_condition.get_tx_receipt(tx_hash)
    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agreement_id,
        20,
        log_event(keeper.access_secret_store_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessSecretStoreCondition.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessSecretStore": 2,
                                                              "escrowReward": 1
                                                              }
                                               }
    tx_hash = keeper.escrow_reward_condition.fulfill(
        agreement_id, price, publisher_acc.address,
        consumer_acc.address, lock_cond_id,
        access_cond_id, publisher_acc
    )
    keeper.escrow_reward_condition.get_tx_receipt(tx_hash)
    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_reward_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessSecretStore": 2,
                                                              "escrowReward": 2
                                                              }
                                               }
