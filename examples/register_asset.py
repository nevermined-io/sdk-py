import logging
import os
from time import sleep

from contracts_lib_py.utils import get_account

from examples import example_metadata, ExampleConfig
from nevermined_sdk_py import Nevermined
from nevermined_sdk_py.config_provider import ConfigProvider

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def register_asset():
    # make nevermined instance
    ConfigProvider.set_config(ExampleConfig.get_config())
    nevermined = Nevermined()
    account = get_account(0)
    # account = ([acc for acc in nevermined.accounts.list() if acc.password] or
    # nevermined.accounts.list())[0]
    ddo = nevermined.assets.create(example_metadata.metadata, account,
                                  providers=['0xfEF2d5e1670342b9EF22eeeDcb287EC526B48095'])

    sleep(ASYNC_DELAY)

    logging.info(f'Registered asset: did={ddo.did}, ddo-services={ddo.services}')
    resolved_ddo = nevermined.assets.resolve(ddo.did)
    logging.info(f'resolved asset ddo: did={resolved_ddo.did}, ddo={resolved_ddo.as_text()}')


if __name__ == '__main__':
    register_asset()
