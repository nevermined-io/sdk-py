import hashlib
import secrets

from tests.resources.helper_functions import get_assset_json_text


def test_ocean_secret_store(publisher_ocean_instance):
    metadata_json = get_assset_json_text(
        'https://raw.githubusercontent.com/keyko-io/nevermind-docs/master/architecture/specs'
        '/examples/access/v0.1/ddo1.json')
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    publisher_account = publisher_ocean_instance.main_account

    encrypt_content = publisher_ocean_instance.secret_store.encrypt(document_id, metadata_json,
                                                                    publisher_account)

    assert metadata_json == publisher_ocean_instance.secret_store.decrypt(document_id,
                                                                          encrypt_content,
                                                                          publisher_account)
