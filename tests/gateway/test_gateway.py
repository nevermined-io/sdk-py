from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.gateway.gateway import Gateway

config = ConfigProvider.get_config()


def test_get_rsa_key():
    assert Gateway.get_rsa_public_key(config)
