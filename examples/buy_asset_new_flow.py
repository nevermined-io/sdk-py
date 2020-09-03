import logging
import os
import time

from contracts_lib_py.diagnostics import Diagnostics
from contracts_lib_py.web3_provider import Web3Provider
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes

from examples import ExampleConfig, example_metadata
from nevermined_sdk_py import ConfigProvider, Nevermined
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from contracts_lib_py.utils import get_account


def _log_event(event_name):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')

    return _process_event


if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def buy_asset_new_flow():
    """
    Requires all Nevermined services running.

    """
    ConfigProvider.set_config(ExampleConfig.get_config())
    config = ConfigProvider.get_config()

    # make nevermined instance
    nevermined = Nevermined()
    Diagnostics.verify_contracts()
    acc = get_account(0)
    if not acc:
        acc = ([acc for acc in nevermined.accounts.list() if acc.password] or nevermined.accounts.list())[0]

    keeper = Keeper.get_instance()
    # Register ddo
    did = ''  # 'did:nv:7648596b60f74301ae1ef9baa5d637255d517ff362434754a3779e1de4c8219b'
    if did:
        ddo = nevermined.assets.resolve(did)
        logging.info(f'using ddo: {did}')
    else:
        ddo = nevermined.assets.create(example_metadata.metadata, acc, providers=[])
        assert ddo is not None, f'Registering asset on-chain failed.'
        did = ddo.did
        logging.info(f'registered ddo: {did}')
        # nevermined here will be used only to publish the asset. Handling the asset by the publisher
        # will be performed by the Gateway server running locally
        provider = '0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0'

        # Wait for did registry event
        event = keeper.did_registry.subscribe_to_event(
            keeper.did_registry.DID_REGISTRY_EVENT_NAME,
            30,
            event_filter={
                '_did': Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
                '_owner': acc.address},
            wait=True
        )
        if not event:
            logging.warning(f'Failed to get the did registry event for asset with did {did}.')
        assert keeper.did_registry.get_block_number_updated(ddo.asset_id) > 0, \
            f'There is an issue in registering asset {did} on-chain.'

        keeper.did_registry.add_provider(ddo.asset_id, provider, acc)
        logging.info(f'is {provider} set as did provider: '
                     f'{keeper.did_registry.is_did_provider(ddo.asset_id, provider)}')

    nevermined_cons = Nevermined()
    consumer_account = get_account(1)

    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    # This will send the order request to Gateway which in turn will execute the agreement on-chain
    nevermined_cons.accounts.request_tokens(consumer_account, 10)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = ''
    if not agreement_id:
        agreement_id = nevermined_cons.assets.order_direct(
            did, sa.index, consumer_account, consumer_account)

    nevermined.assets.access(
        agreement_id,
        did,
        sa.index,
        consumer_account,
        config.downloads_path,
        index=0)
    logging.info('Success buying asset.')

    event = keeper.access_secret_store_condition.subscribe_condition_fulfilled(
        agreement_id, 15, None, (), wait=True
    )
    logging.info(f'Got access event {event}')
    i = 0
    while nevermined.agreements.is_access_granted(
            agreement_id, did, consumer_account.address) is not True and i < 15:
        time.sleep(1)
        i += 1

    assert nevermined.agreements.is_access_granted(agreement_id, did, consumer_account.address)

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
    buy_asset_new_flow()
