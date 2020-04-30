from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from nevermined_sdk_py.nevermined.auth import Auth
from tests.resources.helper_functions import get_publisher_account


def test_get_token():
    auth = Auth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    token = auth.get(acc)
    assert isinstance(token, str), 'Invalid auth token type.'
    assert token.startswith('0x'), 'Invalid auth token.'
    parts = token.split('-')
    assert len(parts) == 2, 'Invalid token, timestamp separator is not found.'

    address = auth.check(token)
    assert address != '0x0', 'Verifying token failed.'


def test_check_token(web3_instance):
    auth = Auth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()

    token = auth.get(acc)
    address = auth.check(token)
    assert address != '0x0', 'Verifying token failed.'

    sig = token.split('-')[0]
    assert auth.check(sig) == '0x0'

    # Test token expiration


def test_store_token():
    auth = Auth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    token = auth.store(acc)
    assert auth.check(token) == acc.address, 'invalid token, check failed.'
    # verify it is saved
    assert auth.restore(acc) == token, 'Restoring token failed.'


def test_restore_token(publisher_instance):
    auth = Auth(Keeper.get_instance(), ':memory:')
    acc = get_publisher_account()
    assert auth.restore(acc) is None, 'Expecting None when restoring non-existing token.'

    token = auth.store(acc)
    assert auth.check(token) == acc.address, 'invalid token, check failed.'
    # verify it is saved
    assert auth.restore(acc) == token, 'Restoring token failed.'
