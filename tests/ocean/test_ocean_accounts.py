#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0


def test_accounts(publisher_ocean_instance):
    for account in publisher_ocean_instance.accounts.list():
        print(account)

    # These accounts have a positive ETH balance
    for account in publisher_ocean_instance.accounts.list():
        assert publisher_ocean_instance.accounts.balance(account).eth >= 0
        assert publisher_ocean_instance.accounts.balance(account).ocn >= 0


def test_token_request(publisher_ocean_instance):
    receiver_account = publisher_ocean_instance.main_account
    # Starting balance for comparison
    start_ocean = publisher_ocean_instance.accounts.balance(receiver_account).ocn

    # Make requests, assert success on request
    publisher_ocean_instance.accounts.request_tokens(receiver_account, 2000)
    # Should be no change, 2000 exceeds the max of 1000
    assert publisher_ocean_instance.accounts.balance(receiver_account).ocn == start_ocean

    amount = 500
    publisher_ocean_instance.accounts.request_tokens(receiver_account, amount)
    # Confirm balance changes
    # TODO Review representation of amounts.
    assert publisher_ocean_instance.accounts.balance(
        receiver_account).ocn == start_ocean + (amount * 1000000000000000000)
