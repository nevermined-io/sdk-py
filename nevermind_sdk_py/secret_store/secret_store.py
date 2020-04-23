"""Secret Store module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging

from eth_utils import remove_0x_prefix
from secret_store_client.client import Client

logger = logging.getLogger(__name__)


class SecretStore(object):
    """Wrapper around the secret store client."""
    _client_class = Client

    def __init__(self, url, parity_url, account):
        """
        :param url: str URL of secret store node to create a document encryption session and store
            the decryption keys
        :param parity_url: str URL of parity/ethereum node to use for
            signing and encryption/decryption
        :param account: Account instance of ethereum account to either encrypt or decrypt a document
        """
        self._secret_store_url = url
        self._parity_node_url = parity_url
        self._account = account

    @staticmethod
    def set_client(secret_store_client):
        """Set a different secret store client.

        :param secret_store_client: SecretStore client
        """
        SecretStore._client_class = secret_store_client

    def _secret_store_client(self, account):
        return SecretStore._client_class(
            self._secret_store_url, self._parity_node_url, account.address, account.password
        )

    def set_secret_store_url(self, url):
        """
        Set secret store url.

        :param url: Url, str
        """
        self._secret_store_url = url

    def encrypt_document(self, document_id, content, threshold=0):
        """
        encrypt string data using the DID as an secret store id,
        if secret store is enabled then return the result from secret store encryption

        None for no encryption performed

        :param document_id: hex str id of document to use for encryption session
        :param content: str to be encrypted
        :param threshold: int
        :return:
            None -- if encryption failed
            hex str -- the encrypted document
        """
        return self._secret_store_client(self._account).publish_document(
            remove_0x_prefix(document_id), content, threshold
        )

    def decrypt_document(self, document_id, encrypted_content):
        """
        Decrypt a previously encrypted content using the secret store keys identified
        by document_id.

        Note that decryption requires permission already granted to the consumer account.

        :param document_id: hex str id of document to use for encryption session
        :param encrypted_content: hex str -- the encrypted content from a previous
            `encrypt_document` operation
        :return:
            None -- if decryption failed
            str -- the original content that was encrypted previously
        """
        return self._secret_store_client(self._account).decrypt_document(
            remove_0x_prefix(document_id),
            encrypted_content
        )
