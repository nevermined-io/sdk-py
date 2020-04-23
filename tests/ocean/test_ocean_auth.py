from nevermind_sdk_py.ocean.keeper import SquidKeeper as Keeper
from nevermind_sdk_py.ocean.ocean_auth import OceanAuth
from tests.resources.helper_functions import get_publisher_account


def test_get_token():
    ocn_auth = OceanAuth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    token = ocn_auth.get(acc)
    assert isinstance(token, str), 'Invalid auth token type.'
    assert token.startswith('0x'), 'Invalid auth token.'
    parts = token.split('-')
    assert len(parts) == 2, 'Invalid token, timestamp separator is not found.'

    address = ocn_auth.check(token)
    assert address != '0x0', 'Verifying token failed.'


def test_check_token(web3_instance):
    ocn_auth = OceanAuth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()

    token = ocn_auth.get(acc)
    address = ocn_auth.check(token)
    assert address != '0x0', 'Verifying token failed.'

    sig = token.split('-')[0]
    assert ocn_auth.check(sig) == '0x0'

    # Test token expiration


def test_store_token():
    ocn_auth = OceanAuth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    token = ocn_auth.store(acc)
    assert ocn_auth.check(token) == acc.address, 'invalid token, check failed.'
    # verify it is saved
    assert ocn_auth.restore(acc) == token, 'Restoring token failed.'


def test_restore_token(publisher_ocean_instance):
    ocn_auth = OceanAuth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    assert ocn_auth.restore(acc) is None, 'Expecting None when restoring non-existing token.'

    token = ocn_auth.store(acc)
    assert ocn_auth.check(token) == acc.address, 'invalid token, check failed.'
    # verify it is saved
    assert ocn_auth.restore(acc) == token, 'Restoring token failed.'
