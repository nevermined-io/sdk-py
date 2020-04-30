from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper


def test_get_condition_name_by_address():
    keeper = Keeper.get_instance()
    name = keeper.get_condition_name_by_address(keeper.lock_reward_condition.address)
    assert name == 'lockReward'

    name = keeper.get_condition_name_by_address(keeper.access_secret_store_condition.address)
    assert name == 'accessSecretStore'

    name = keeper.get_condition_name_by_address(keeper.escrow_reward_condition.address)
    assert name == 'escrowReward'
