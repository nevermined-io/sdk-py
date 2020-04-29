import logging
import os
from time import sleep

from contracts_lib_py.utils import get_account

from examples import example_metadata, ExampleConfig
from nevermind_sdk_py import Nevermind
from nevermind_sdk_py.config_provider import ConfigProvider

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def register_asset():
    # make nevermind instance
    ConfigProvider.set_config(ExampleConfig.get_config())
    nevermind = Nevermind()
    account = get_account(0)
    # account = ([acc for acc in nevermind.accounts.list() if acc.password] or
    # nevermind.accounts.list())[0]
    ddo = nevermind.assets.create(example_metadata.metadata, account,
                                  providers=['0xfEF2d5e1670342b9EF22eeeDcb287EC526B48095'])

    sleep(ASYNC_DELAY)

    logging.info(f'Registered asset: did={ddo.did}, ddo-services={ddo.services}')
    resolved_ddo = nevermind.assets.resolve(ddo.did)
    logging.info(f'resolved asset ddo: did={resolved_ddo.did}, ddo={resolved_ddo.as_text()}')


if __name__ == '__main__':
    register_asset()
