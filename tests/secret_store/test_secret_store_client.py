import hashlib
import secrets
from unittest.mock import MagicMock, Mock

from contracts_lib_py.account import Account

from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.secret_store.secret_store import SecretStore
from tests.resources.helper_functions import get_assset_json_text


def test_secret_store_encrypt_decrypt():
    metadata_json = get_assset_json_text(
        'https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo1.json')
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    print(document_id)
    config = ConfigProvider.get_config()
    ss_client = Mock
    ss_client.publish_document = MagicMock(return_value='!!document!!')
    ss_client.decrypt_document = MagicMock(return_value=metadata_json)
    SecretStore.set_client(ss_client)

    ss_args = (config.secret_store_url, config.parity_url, Account('0x0000', 'aaa'))
    result = SecretStore(*ss_args).encrypt_document(document_id, metadata_json)
    print(result)
    assert SecretStore(*ss_args).decrypt_document(document_id, result) == metadata_json


def test_set_secret_store_url():
    ss_client = Mock
    SecretStore.set_client(ss_client)
    SecretStore.set_secret_store_url(ss_client, url='http://secret-store-changed-url')
    assert ss_client._secret_store_url == 'http://secret-store-changed-url'


def test_set_client():
    pass
