#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
from time import sleep

from examples import ExampleConfig, example_metadata
from contracts_lib_py.utils import get_account
from nevermind_sdk_py import Ocean
from nevermind_sdk_py.config_provider import ConfigProvider

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def register_asset():
    # make ocean instance
    ConfigProvider.set_config(ExampleConfig.get_config())
    ocn = Ocean()
    account = get_account(0)
    # account = ([acc for acc in ocn.accounts.list() if acc.password] or ocn.accounts.list())[0]
    ddo = ocn.assets.create(example_metadata.metadata, account, providers=['0xfEF2d5e1670342b9EF22eeeDcb287EC526B48095'])

    sleep(ASYNC_DELAY)

    logging.info(f'Registered asset: did={ddo.did}, ddo-services={ddo.services}')
    resolved_ddo = ocn.assets.resolve(ddo.did)
    logging.info(f'resolved asset ddo: did={resolved_ddo.did}, ddo={resolved_ddo.as_text()}')


if __name__ == '__main__':
    register_asset()
