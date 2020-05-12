import json
import logging
import os
import re

from contracts_lib_py.utils import add_ethereum_prefix_and_hash_msg
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.exceptions import (EncryptAssetUrlsError,
                                    InitializeServiceAgreementError)
from common_utils_py.http_requests.requests_session import get_requests_session

from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper

logger = logging.getLogger(__name__)


class Gateway:
    """
    `Gateway` is the name chosen for the asset service provider.

    The main functions available are:
    - initialize_service_agreement
    - consume_service
    - run_compute_service (not implemented yet)

    """
    _http_client = get_requests_session()

    @staticmethod
    def set_http_client(http_client):
        """Set the http client to something other than the default `requests`"""
        Gateway._http_client = http_client

    @staticmethod
    def encrypt_files_dict(files_dict, encrypt_endpoint, asset_id, account_address, signed_did):
        payload = json.dumps({
            'documentId': asset_id,
            'signedDocumentId': signed_did,
            'document': json.dumps(files_dict),
            'publisherAddress': account_address
        })
        response = Gateway._http_client.post(
            encrypt_endpoint, data=payload,
            headers={'content-type': 'application/json'}
        )
        if response and hasattr(response, 'status_code'):
            if response.status_code != 201:
                msg = (f'Encrypt file urls failed at the encryptEndpoint '
                       f'{encrypt_endpoint}, reason {response.text}, status {response.status_code}'
                       )
                logger.error(msg)
                raise EncryptAssetUrlsError(msg)

            logger.info(
                f'Asset urls encrypted successfully, encrypted urls str: {response.text},'
                f' encryptedEndpoint {encrypt_endpoint}')

            return response.text

    @staticmethod
    def initialize_service_agreement(did, agreement_id, service_index, signature,
                                     account_address,
                                     purchase_endpoint):
        """
        Send a request to the service provider (purchase_endpoint) to initialize the service
        agreement for the asset identified by `did`.

        :param did: id of the asset includes the `did:nv:` prefix, str
        :param agreement_id: id of the agreement, hex str
        :param service_index: identifier of the service inside the asset DDO, str
        :param signature: signed agreement hash, hex str
        :param account_address: ethereum address of the consumer signing this agreement, hex str
        :param purchase_endpoint: url of the service provider, str
        :return: bool
        """
        payload = Gateway._prepare_consume_payload(
            did, agreement_id, service_index, signature, account_address
        )
        response = Gateway._http_client.post(
            purchase_endpoint, data=payload,
            headers={'content-type': 'application/json'}
        )
        if response and hasattr(response, 'status_code'):
            if response.status_code != 201:
                msg = (f'Initialize service agreement failed at the purchaseEndpoint '
                       f'{purchase_endpoint}, reason {response.text}, status {response.status_code}'
                       )
                logger.error(msg)
                raise InitializeServiceAgreementError(msg)

            logger.info(
                f'Service agreement initialized successfully, service agreement id {agreement_id},'
                f' purchaseEndpoint {purchase_endpoint}')
            return True

    @staticmethod
    def consume_service(service_agreement_id, service_endpoint, account, files,
                        destination_folder, index=None):
        """
        Call the Gateway endpoint to get access to the different files that form the asset.

        :param service_agreement_id: Service Agreement Id, str
        :param service_endpoint: Url to consume, str
        :param account: Account instance of the consumer signing this agreement, hex-str
        :param files: List containing the files to be consumed, list
        :param index: Index of the document that is going to be downloaded, int
        :param destination_folder: Path, str
        :return: True if was downloaded, bool
        """
        signature = Keeper.get_instance().sign_hash(
            add_ethereum_prefix_and_hash_msg(service_agreement_id),
            account)

        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
            assert index < len(files), logger.error(
                'index can not be bigger than the number of files')
            consume_url = Gateway._create_consume_url(service_endpoint, service_agreement_id, account,
                                                      None, signature, index)
            logger.info(f'invoke consume endpoint with this url: {consume_url}')
            response = Gateway._http_client.get(consume_url, stream=True)
            file_name = Gateway._get_file_name(response)
            Gateway.write_file(response, destination_folder, file_name)
        else:
            for i, _file in enumerate(files):
                consume_url = Gateway._create_consume_url(service_endpoint, service_agreement_id,
                                                          account, _file,
                                                          signature, i)
                logger.info(f'invoke consume endpoint with this url: {consume_url}')
                response = Gateway._http_client.get(consume_url, stream=True)
                file_name = Gateway._get_file_name(response)
                Gateway.write_file(response, destination_folder, file_name or f'file-{i}')

    @staticmethod
    def execute_service(service_agreement_id, service_endpoint, account, workflow_ddo):
        """

        :param service_agreement_id:
        :param service_endpoint:
        :param account:
        :return:
        """
        signature = Keeper.get_instance().sign_hash(
            add_ethereum_prefix_and_hash_msg(service_agreement_id),
            account)
        execute_url = Gateway._create_execute_url(service_endpoint, service_agreement_id, account,
                                                  workflow_ddo.did, signature)
        logger.info(f'invoke execute endpoint with this url: {execute_url}')
        response = Gateway._http_client.post(execute_url)

    @staticmethod
    def _prepare_consume_payload(did, service_agreement_id, service_index, signature,
                                 consumer_address):
        """Prepare a payload to send to Nevermined Gateway.

        :param did: DID, str
        :param service_agreement_id: Service Agreement Id, str
        :param service_index: identifier of the service inside the asset DDO, str
        service in the DDO (DID document)
        :param signature: the signed agreement message hash which includes
         conditions and their parameters values and other details of the agreement, str
        :param consumer_address: ethereum address of the consumer signing this agreement, hex-str
        :return: dict
        """
        return json.dumps({
            'did': did,
            'serviceAgreementId': service_agreement_id,
            ServiceAgreement.SERVICE_INDEX: service_index,
            'signature': signature,
            'consumerAddress': consumer_address
        })

    @staticmethod
    def get_gateway_url(config):
        """
        Return the Gateway component url.

        :param config: Config
        :return: Url, str
        """
        gateway_url = 'http://localhost:8030'
        if config.has_option('resources', 'gateway.url'):
            gateway_url = config.get('resources', 'gateway.url') or gateway_url

        gateway_path = '/api/v1/gateway'
        return f'{gateway_url}{gateway_path}'

    @staticmethod
    def get_purchase_endpoint(config):
        """
        Return the endpoint to consume the asset.

        :param config:Config
        :return: Url, str
        """
        return f'{Gateway.get_gateway_url(config)}/services/access/initialize'

    @staticmethod
    def get_consume_endpoint(config):
        """
        Return the url to consume the asset.

        :param config: Config
        :return: Url, str
        """
        return f'{Gateway.get_gateway_url(config)}/services/consume'

    @staticmethod
    def get_execute_endpoint(config):
        """
        Return the url to execute the asset.

        :param config: Config
        :return: Url, str
        """
        return f'{Gateway.get_gateway_url(config)}/services/exec'

    @staticmethod
    def get_encrypt_endpoint(config):
        """
        Return the url to encrypt the asset.

        :param config: Config
        :return: Url, str
        """
        return f'{Gateway.get_gateway_url(config)}/services/publish'

    @staticmethod
    def _get_file_name(response):
        try:
            return re.match(r'attachment;filename=(.+)',
                            response.headers.get('content-disposition'))[1]
        except Exception as e:
            logger.warning(f'It was not possible to get the file name. {e}')

    @staticmethod
    def write_file(response, destination_folder, file_name):
        """
        Write the response content in a file in the destination folder.
        :param response: Response
        :param destination_folder: Destination folder, string
        :param file_name: File name, string
        :return: bool
        """
        if response.status_code == 200:
            with open(os.path.join(destination_folder, file_name), 'wb') as f:
                for chunk in response.iter_content(chunk_size=None):
                    f.write(chunk)
            logger.info(f'Saved downloaded file in {f.name}')
        else:
            logger.warning(f'consume failed: {response.reason}')

    @staticmethod
    def _create_consume_url(service_endpoint, service_agreement_id, account, _file=None,
                            signature=None, index=None):
        if _file is not None and 'url' in _file:
            url = _file['url']
            if url.startswith('"') or url.startswith("'"):
                url = url[1:-1]
            return (f'{service_endpoint}'
                    f'?url={url}'
                    f'&serviceAgreementId={service_agreement_id}'
                    f'&consumerAddress={account.address}'
                    )
        else:
            return (f'{service_endpoint}'
                    f'?signature={signature}'
                    f'&serviceAgreementId={service_agreement_id}'
                    f'&consumerAddress={account.address}'
                    f'&index={index}'
                    )

    @staticmethod
    def _create_execute_url(service_endpoint, service_agreement_id, account, workflow_did,
                            signature=None):
        return (f'{service_endpoint}'
                f'?signature={signature}'
                f'&serviceAgreementId={service_agreement_id}'
                f'&consumerAddress={account.address}'
                f'&workflowDID={workflow_did}')
