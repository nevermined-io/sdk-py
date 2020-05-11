def test_token_request(publisher_instance):
    receiver_account = publisher_instance.main_account
    # Starting balance for comparison
    start_ocean = publisher_instance.accounts.balance(receiver_account).ocn

    # Make requests, assert success on request
    publisher_instance.tokens.request(receiver_account, 2000)
    # Should be no change, 2000 exceeds the max of 1000
    assert publisher_instance.accounts.balance(receiver_account).ocn == start_ocean

    amount = 500
    publisher_instance.tokens.request(receiver_account, amount)
    # Confirm balance changes
    # TODO Review representation of amounts.
    assert publisher_instance.accounts.balance(
        receiver_account).ocn == start_ocean + (amount * 1000000000000000000)


def test_transfer_tokens(publisher_instance_no_init, consumer_instance_no_init):
    receiver_account = publisher_instance_no_init.main_account
    sender_account = consumer_instance_no_init.main_account

    receiver_start_balance = publisher_instance_no_init.accounts.balance(receiver_account).ocn
    sender_start_balance = consumer_instance_no_init.accounts.balance(sender_account).ocn

    consumer_instance_no_init.tokens.transfer(receiver_account.address, 500, sender_account)

    assert publisher_instance_no_init.accounts.balance(
        receiver_account).ocn == receiver_start_balance + 500
    assert consumer_instance_no_init.accounts.balance(
        sender_account).ocn == sender_start_balance - 500
