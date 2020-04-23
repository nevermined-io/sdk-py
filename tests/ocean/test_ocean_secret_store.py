#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import secrets

from tests.resources.helper_functions import get_resource_path


def test_ocean_secret_store(publisher_ocean_instance):
    test_document = get_resource_path('ddo', 'ddo_sample1.json')
    with open(test_document, 'r') as file_handle:
        metadata = json.load(file_handle)
    metadata_json = json.dumps(metadata)
    document_id = hashlib.sha256((metadata_json + secrets.token_hex(32)).encode()).hexdigest()
    publisher_account = publisher_ocean_instance.main_account

    encrypt_content = publisher_ocean_instance.secret_store.encrypt(document_id, metadata_json,
                                                                    publisher_account)

    assert metadata_json == publisher_ocean_instance.secret_store.decrypt(document_id,
                                                                          encrypt_content,
                                                                          publisher_account)
