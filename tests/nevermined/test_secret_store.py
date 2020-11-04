import hashlib
import secrets

from tests.resources.helper_functions import get_assset_json_text


def test_secret_store(publisher_instance):
    metadata_json = get_assset_json_text(
        'https://raw.githubusercontent.com/nevermined-io/docs/master/docs/architecture/specs'
        '/examples/access/v0.1/ddo1.json')
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    publisher_account = publisher_instance.main_account

    encrypt_content = publisher_instance.secret_store.encrypt(document_id, metadata_json,
                                                              publisher_account)

    assert metadata_json == publisher_instance.secret_store.decrypt(document_id,
                                                                    encrypt_content,
                                                                    publisher_account)
