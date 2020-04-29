import logging
import os
from time import sleep

from contracts_lib_py.utils import get_account

from examples import example_metadata, ExampleConfig
from nevermind_sdk_py import ConfigProvider, Nevermind

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def resolve_asset():
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


if __name__ == '__main__':
    resolve_asset()
