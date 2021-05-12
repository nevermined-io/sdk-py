import json
import logging
import os

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.did import did_to_id

logger = logging.getLogger(__name__)


class AssetConsumer:

    @staticmethod
    def access(service_agreement_id, service_index, ddo, consumer_account, destination,
                 gateway, secret_store, config, index=None, service_type=ServiceTypes.ASSET_ACCESS):
        """
        Download asset data files or result files from a compute job.

        :param service_agreement_id: Service agreement id, str
        :param service_index: identifier of the service inside the asset DDO, str
        :param ddo: DDO
        :param consumer_account: Account instance of the consumer
        :param destination: Path, str
        :param gateway: Gateway instance
        :param secret_store: SecretStore instance
        :param config: Sdk configuration instance
        :param index: Index of the document that is going to be downloaded, int
        :param service_type: service type
        :return: Asset folder path, str
        """
        did = ddo.did
        sa = ServiceAgreement.from_ddo(service_type, ddo)
        consume_url = sa.service_endpoint
        if not consume_url:
            logger.error(
                'Consume asset failed, service definition is missing the "serviceEndpoint".')
            raise AssertionError(
                'Consume asset failed, service definition is missing the "serviceEndpoint".')

        if ddo.get_service(ServiceTypes.AUTHORIZATION):
            secret_store_service = ddo.get_service(service_type=ServiceTypes.AUTHORIZATION)
            secret_store_url = secret_store_service.service_endpoint
            secret_store.set_secret_store_url(secret_store_url)

        asset_folder = create_asset_folder(did, service_index, destination)

        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
            assert index < len(ddo.metadata['main']['files']), logger.error(
                'index can not be bigger than the number of files')

        if service_type is ServiceTypes.NFT_ACCESS:
            uri = '/nft-access'
        else:
            uri = '/access'

        if index is not None:
            gateway.access_service(
                did,
                service_agreement_id,
                consume_url,
                consumer_account,
                asset_folder,
                config,
                index,
                uri
            )
        else:
            for i, _file in enumerate(ddo.metadata['main']['files']):
                gateway.access_service(
                    did,
                    service_agreement_id,
                    consume_url,
                    consumer_account,
                    asset_folder,
                    config,
                    i,
                    uri
                )

        return asset_folder

    @staticmethod
    def download(service_index, ddo, owner_account, destination,
                 gateway, secret_store, config, index=None):
        """
        Allows the onwer of and asset to download the data files.

        :param service_index: identifier of the service inside the asset DDO, str
        :param ddo: DDO
        :param owner_account: Account instance of the owner
        :param destination: Path, str
        :param gateway: Gateway instance
        :param secret_store: SecretStore instance
        :param config: Sdk configuration instance
        :param index: Index of the document that is going to be downloaded, int
        :return: Asset folder path, str
        """
        did = ddo.did
        if ddo.get_service(ServiceTypes.AUTHORIZATION):
            secret_store_service = ddo.get_service(service_type=ServiceTypes.AUTHORIZATION)
            secret_store_url = secret_store_service.service_endpoint
            secret_store.set_secret_store_url(secret_store_url)

        asset_folder = create_asset_folder(did, service_index, destination)

        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
            assert index < len(ddo.metadata['main']['files']), logger.error(
                'index can not be bigger than the number of files')
        if index is not None:
            gateway.download(
                did,
                owner_account,
                asset_folder,
                index,
                config
            )
        else:
            for i, _file in enumerate(ddo.metadata['main']['files']):
                gateway.download(
                    did,
                    owner_account,
                    asset_folder,
                    i,
                    config
                )

        return asset_folder

    @staticmethod
    def compute_logs(service_agreement_id, execution_id, account, gateway, config):
        """
        Get the logs of a compute workflow.

        :param service_agreement_id: The id of the service agreement that ordered the compute job, str
        :param execution_id: The id of the compute job, str
        :param account: Account instance that ordered the execution of the compute job
        :param gateway: Gateway instance
        :param config: Sdk configuration instance
        :return: list, compute logs
        """
        return gateway.compute_logs(service_agreement_id, execution_id, account, config).json()

    @staticmethod
    def compute_status(service_agreement_id, execution_id, account, gateway, config):
        """
        Get the status of a compute workflow.

        :param service_agreement_id: The id of the service agreement that ordered the compute job, str
        :param execution_id: The id of the compute job, str
        :param account: Account instance that ordered the execution of the compute job
        :param gateway: Gateway instance
        :param config: Sdk configuration instance
        :return: dict, compute logs
        """
        return gateway.compute_status(service_agreement_id, execution_id, account, config).json()

def create_asset_folder(did, service_index, destination):
    """
    Creates the asset folder to download the assets

    :param did: the identifier of the asset ddo.
    :param service_index: identifier of the service inside the asset DDO, str
    :param destination: Path, str
    :return: Asset folder path, str
    """
    if not os.path.isabs(destination):
        destination = os.path.abspath(destination)
    if not os.path.exists(destination):
        os.mkdir(destination)

    asset_folder = os.path.join(destination,
                                f'datafile.{did_to_id(did)}.{service_index}')
    if not os.path.exists(asset_folder):
        os.mkdir(asset_folder)

    return asset_folder
