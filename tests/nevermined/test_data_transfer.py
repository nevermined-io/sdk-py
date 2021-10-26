from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes, ServiceTypesIndices
from common_utils_py.utils.utilities import to_checksum_addresses
from web3 import providers

from nevermined_sdk_py.gateway.gateway import Gateway
from nevermined_sdk_py.nevermined.agreements import check_token_address
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import get_buyer_public_key, get_key, get_provider_babyjub_key, get_provider_public_key, log_event
from tests.resources.mocks.gateway_mock import GatewayMock
from tests.resources.snark_util import call_prover

def test_sign_agreement(publisher_instance, consumer_instance, proof_ddo):
    # point consumer_instance's Gateway mock to the publisher's nevermined instance
    Gateway.set_http_client(
        GatewayMock(publisher_instance, publisher_instance.main_account))

    consumer_acc = consumer_instance.main_account
    keeper = Keeper.get_instance()

    publisher_acc = publisher_instance.main_account

    did = proof_ddo.did
    asset_id = proof_ddo.asset_id
    ddo = consumer_instance.assets.resolve(did)
    service_agreement = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS_PROOF, ddo)

    price = service_agreement.get_price()

    # Give consumer some tokens
    keeper.dispenser.request_vodkas(price * 2, consumer_acc)
    consumer_acc.babyjub_address = get_buyer_public_key()
    publisher_acc.babyjub_address = get_provider_public_key()
    provider_secret = get_provider_babyjub_key().secret
    proof = call_prover(consumer_acc.babyjub_address, provider_secret, '0x'+get_key())

    agreement_id, signature = consumer_instance.agreements.prepare(
        did, consumer_acc, ServiceTypesIndices.DEFAULT_ACCESS_PROOF_INDEX)

    success = publisher_instance.agreements.create(
        did,
        ServiceTypesIndices.DEFAULT_ACCESS_PROOF_INDEX,
        agreement_id,
        consumer_acc,
        publisher_acc
    )
    assert success, 'createAgreement failed.'

    # Verify condition types (condition contracts)
    agreement_values = keeper.agreement_manager.get_agreement(agreement_id)
    assert agreement_values.did == asset_id, ''
    cond_types = keeper.access_proof_template.get_condition_types()
    for i, cond_id in enumerate(agreement_values.condition_ids):
        cond = keeper.condition_manager.get_condition(cond_id)
        assert cond.type_ref == cond_types[i]

    access_cond_id, lock_cond_id, escrow_cond_id = agreement_values.condition_ids

    # Fulfill lock_payment_condition is done automatically when create agreement is done correctly
    assert 2 == keeper.condition_manager.get_condition_state(lock_cond_id), ''
    assert 1 == keeper.condition_manager.get_condition_state(access_cond_id), ''
    assert 1 == keeper.condition_manager.get_condition_state(escrow_cond_id), ''

    # Fulfill access_condition
    tx_hash = keeper.access_proof_condition.fulfill(
        agreement_id, proof['hash'], consumer_acc.babyjub_address, publisher_acc.babyjub_address, proof['cipher'], proof['proof'], publisher_acc
    )
    keeper.access_proof_condition.get_tx_receipt(tx_hash)
    assert 2 == keeper.condition_manager.get_condition_state(access_cond_id), ''
    event = keeper.access_proof_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.access_proof_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessSecretStoreCondition.Fulfilled'

    # Fulfill escrow_payment_condition

    amounts = service_agreement.get_amounts_int()
    receivers = service_agreement.get_receivers()
    token_address = check_token_address(
        keeper, service_agreement.get_param_value_by_name('_tokenAddress'))

    tx_hash = keeper.escrow_payment_condition.fulfill(
        agreement_id, asset_id, amounts, receivers,
        keeper.escrow_payment_condition.address, token_address, lock_cond_id,
        access_cond_id, publisher_acc
    )
    keeper.escrow_payment_condition.get_tx_receipt(tx_hash)
    assert 2 == keeper.condition_manager.get_condition_state(escrow_cond_id), ''
    event = keeper.escrow_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_payment_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    publisher_instance.assets.retire(did)


def test_agreement_status(setup_agreements_proof_environment, agreements):
    (
        keeper,
        publisher_acc,
        consumer_acc,
        agreement_id,
        asset_id,
        price,
        service_agreement,
        (lock_cond_id, access_cond_id, escrow_cond_id),

    ) = setup_agreements_proof_environment

    consumer_acc.babyjub_address = get_buyer_public_key()
    publisher_acc.babyjub_address = get_provider_public_key()
    provider_secret = get_provider_babyjub_key().secret
    proof = call_prover(consumer_acc.babyjub_address, provider_secret, '0x'+get_key())

    success = keeper.access_proof_template.create_agreement(
        agreement_id,
        asset_id,
        [access_cond_id, lock_cond_id, escrow_cond_id],
        service_agreement.conditions_timelocks,
        service_agreement.conditions_timeouts,
        consumer_acc.address,
        publisher_acc
    )
    assert success, f'createAgreement failed {success}'
    event = keeper.access_proof_template.subscribe_agreement_created(
        agreement_id,
        10,
        log_event(keeper.access_proof_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AgreementCreated '
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 1,
                                                              "accessProof": 1,
                                                              "escrowReward": 1
                                                              }
                                               }

    amounts = service_agreement.get_amounts_int()
    receivers = service_agreement.get_receivers()

    token_address = keeper.token.address

    agreements.conditions.lock_payment(
        agreement_id, asset_id, amounts, receivers, token_address, consumer_acc)

    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.lock_payment_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessProof": 1,
                                                              "escrowReward": 1
                                                              }
                                               }
    tx_hash = keeper.access_proof_condition.fulfill(
        agreement_id, proof['hash'], consumer_acc.babyjub_address, publisher_acc.babyjub_address, proof['cipher'], proof['proof'], publisher_acc
    )
    keeper.access_proof_condition.get_tx_receipt(tx_hash)
    event = keeper.access_proof_condition.subscribe_condition_fulfilled(
        agreement_id,
        20,
        log_event(keeper.access_proof_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AccessProofCondition.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessProof": 2,
                                                              "escrowReward": 1
                                                              }
                                               }

    tx_hash = keeper.escrow_payment_condition.fulfill(
        agreement_id, asset_id, amounts, receivers,
        keeper.escrow_payment_condition.address, token_address, lock_cond_id,
        access_cond_id, publisher_acc
    )
    keeper.escrow_payment_condition.get_tx_receipt(tx_hash)
    event = keeper.escrow_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.escrow_payment_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    assert agreements.status(agreement_id) == {"agreementId": agreement_id,
                                               "conditions": {"lockReward": 2,
                                                              "accessProof": 2,
                                                              "escrowReward": 2
                                                              }
                                               }
