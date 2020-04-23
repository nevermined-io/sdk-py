#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
from time import sleep

from contracts_lib_py.utils import get_account

from examples import example_metadata, ExampleConfig
from nevermind_sdk_py import ConfigProvider, Ocean

if 'TEST_NILE' in os.environ and os.environ['TEST_NILE'] == '1':
    ASYNC_DELAY = 5  # seconds
else:
    ASYNC_DELAY = 1  # seconds


def sign_service_agreement():
    ConfigProvider.set_config(ExampleConfig.get_config())
    # make ocean instance and register an asset
    ocn = Ocean()
    acc = get_account(0)
    ddo = ocn.assets.create(example_metadata.metadata, acc)

    consumer_account = get_account(1)
    agreement_id, signature = ocn.agreements.prepare(
        ddo.did,
        consumer_account
    )

    sleep(ASYNC_DELAY)

    logging.info(f'service agreement signed: '
                 f'\nservice agreement id: {agreement_id}, '
                 f'\nsignature: {signature}')


if __name__ == '__main__':
    sign_service_agreement()
