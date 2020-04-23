#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

class SecretStoreMock:
    args = None
    id_to_document = dict()

    def __init__(self, secret_store_url, keeper_url, account):
        self.args = (secret_store_url, keeper_url, account)

    def set_secret_store_url(self, url):
        return

    def encrypt_document(self, document_id, document, threshold=0):
        encrypted = f'{self}.{document_id}!!{document}!!{threshold}'
        self.id_to_document[document_id] = (document, encrypted)
        return encrypted

    def decrypt_document(self, document_id, encrypted_document):
        doc, encrypted = self.id_to_document.get(document_id)
        assert encrypted == encrypted_document
        return doc
