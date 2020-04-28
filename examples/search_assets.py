"""Example of searching an asset in Nevermind."""
import logging
import os
from time import sleep
from contracts_lib_py.utils import get_account

from examples import ExampleConfig, example_metadata
from nevermind_sdk_py import ConfigProvider, Nevermind

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def search_assets():
    ConfigProvider.set_config(ExampleConfig.get_config())
    nevermind = Nevermind()
    account = get_account(0)
    ddo = nevermind.assets.create(
        example_metadata.metadata, account,
    )

    sleep(ASYNC_DELAY)

    logging.info(f'Registered asset: did={ddo.did}, ddo={ddo.as_text()}')
    resolved_ddo = nevermind.assets.resolve(ddo.did)
    logging.info(f'resolved asset ddo: did={resolved_ddo.did}, ddo={resolved_ddo.as_text()}')

    ddo_list = nevermind.assets.search('bonding curve')
    logging.info(f'found {len(ddo_list)} assets that contain `bonding curve` in their metadata.')
    ddo_list = nevermind.assets.query(
        {"query": {"text": ['Nevermind protocol white paper']}})
    logging.info(
        f'found {len(ddo_list)} assets with name that contains `Nevermind protocol white paper`')


if __name__ == '__main__':
    search_assets()
