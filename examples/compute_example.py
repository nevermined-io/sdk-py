import logging
import time
import json

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from contracts_lib_py.utils import get_account
from contracts_lib_py.web3_provider import Web3Provider

from examples import example_metadata, ExampleConfig
from nevermined_sdk_py import ConfigProvider, Nevermined
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper

logging.basicConfig(level=logging.INFO)

def _log_event(event_name):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')

    return _process_event

def wait_for_registry_event(keeper, owner, ddo, timeout=30):
    # Wait for did registry event
    event = keeper.did_registry.subscribe_to_event(
        keeper.did_registry.DID_REGISTRY_EVENT_NAME,
        30,
        event_filter={
            '_did': Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id)},
        wait=True
    )
    if not event:
        logging.warning(f'Failed to get the did registry event for asset with did {ddo.did}.')
    assert keeper.did_registry.get_block_number_updated(ddo.asset_id) > 0, \
        f'There is an issue in registering asset {ddo.did} on-chain.'
    print(event)

def compute_example():
    ConfigProvider.set_config(ExampleConfig.get_config())
    config = ConfigProvider.get_config()

    # make nevermined instance
    nevermined = Nevermined()
    acc = get_account(0)
    if not acc:
        acc = \
        ([acc for acc in nevermined.accounts.list() if acc.password] or nevermined.accounts.list())[
            0]
    keeper = Keeper.get_instance()
    provider = '0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0'
    print(f'provider: {provider}')
    print(f'address: {acc.address}')
    print(f'keyfile: {acc.key_file}')

    ddo = nevermined.assets.create(example_metadata.metadata, acc, providers=[provider],
                                   authorization_type='SecretStore')
    print(f'provider {provider}')
    assert ddo is not None, f'Registering asset on-chain failed.'
    wait_for_registry_event(keeper, acc, ddo)
    did = ddo.did
    logging.info(f'registered ddo: {did}')

    compute_ddo = nevermined.assets.create(example_metadata.compute_ddo, acc, providers=[provider],
                                           authorization_type='SecretStore')
    print(f'provider: {provider}')
    assert compute_ddo is not None, f'Registering asset on-chain failed.'
    wait_for_registry_event(keeper, acc, compute_ddo)
    compute_did = compute_ddo.did
    logging.info(f'registered ddo: {compute_did}')

    algo_ddo = nevermined.assets.create(example_metadata.algo_metadata, acc, providers=[provider],
                                        authorization_type='SecretStore')
    print(f'provider: {provider}')
    assert algo_ddo is not None, f'Registering algorithm on-chain failed.'
    wait_for_registry_event(keeper, acc, algo_ddo)
    algo_did = algo_ddo.did
    logging.info(f'registered ddo: {algo_did}')

    workflow_metadata = example_metadata.workflow_ddo
    workflow_metadata['main']['workflow']['stages'][0]['input'][0]['id'] = did
    workflow_metadata['main']['workflow']['stages'][0]['input'][1]['id'] = compute_did
    workflow_metadata['main']['workflow']['stages'][0]['transformation']['id'] = algo_did
    workflow_ddo = nevermined.assets.create(workflow_metadata, acc, providers=[provider],
                                            authorization_type='SecretStore')
    print(f'provider: {provider}')

    print("\n\nMetadata ddo:\n\n")
    print(json.dumps(ddo.as_dictionary(), indent=2))
    print("\n\nCompute ddo:\n\n")
    print(json.dumps(compute_ddo.as_dictionary(), indent=2))
    print("\n\nAlgo ddo:\n\n")
    print(json.dumps(algo_ddo.as_dictionary(), indent=2))
    print("\n\nWorkflow ddo:\n\n")
    print(json.dumps(workflow_ddo.as_dictionary(), indent=2))
    assert workflow_ddo is not None, f'Registering algorithm on-chain failed.'
    wait_for_registry_event(keeper, acc, workflow_ddo)
    algo_did = algo_ddo.did
    workflow_did = workflow_ddo.did
    logging.info(f'registered ddo: {workflow_did}')

    nevermined_cons = Nevermined()
    consumer_account = get_account(1)

    service = compute_ddo.get_service(service_type=ServiceTypes.CLOUD_COMPUTE)
    nevermined_cons.accounts.request_tokens(consumer_account, 10)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = ''
    if not agreement_id:
        agreement_id = nevermined_cons.assets.order(
            compute_did, sa.index, consumer_account)

    logging.info('placed order: %s, %s', did, agreement_id)

    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event, "Lock reward condition fulfilled event is not found, check the keeper node's logs"
    logging.info('Got lock reward event, next: wait for the access condition..')

    event = keeper.compute_execution_condition.subscribe_condition_fulfilled(
        agreement_id, 15, None, (), wait=True
    )
    logging.info(f'Got access event {event}')

    nevermined_cons.assets.execute(agreement_id, compute_did, sa.index, consumer_account,
                                   workflow_did)
    logging.info('Success executing workflow.')

    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id,
        30,
        None,
        (),
        wait=True
    )
    assert event, 'no event for EscrowReward.Fulfilled'
    logging.info(f'got EscrowReward.FULFILLED event: {event}')
    logging.info('Done buy asset.')


if __name__ == '__main__':
    compute_example()
