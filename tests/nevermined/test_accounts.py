import pytest

def test_accounts(publisher_instance):
    for account in publisher_instance.accounts.list():
        print(account)

    # These accounts have a positive ETH balance
    for account in publisher_instance.accounts.list():
        assert publisher_instance.accounts.balance(account).eth >= 0
        assert publisher_instance.accounts.balance(account).ocn >= 0


def test_token_request(publisher_instance):
    receiver_account = publisher_instance.main_account
    # Starting balance for comparison
    start_ocean = publisher_instance.accounts.balance(receiver_account).ocn

    # Make requests, assert success on request
    publisher_instance.accounts.request_tokens(receiver_account, 2000)
    # Should be no change, 2000 exceeds the max of 1000
    assert publisher_instance.accounts.balance(receiver_account).ocn == start_ocean

    amount = 500
    publisher_instance.accounts.request_tokens(receiver_account, amount)
    # Confirm balance changes
    # TODO Review representation of amounts.
    assert publisher_instance.accounts.balance(
        receiver_account).ocn == start_ocean + (amount * 1000000000000000000)


@pytest.mark.skip(reason="It is only possible request once per 24hours")
def test_request_eth_from_faucet(consumer_instance):
    receiver_account = consumer_instance.main_account

    assert consumer_instance.accounts.request_eth_from_faucet(receiver_account.address)
