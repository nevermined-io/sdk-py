import copy
import json
import logging
import os

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_factory import ServiceDescriptor, ServiceFactory
from common_utils_py.agreements.service_types import ServiceAuthorizationTypes, ServiceTypes
from common_utils_py.ddo.ddo import DDO
from common_utils_py.ddo.metadata import MetadataMain
from common_utils_py.ddo.public_key_rsa import PUBLIC_KEY_TYPE_RSA
from common_utils_py.did import DID, did_to_id, did_to_id_bytes, convert_to_bytes
from common_utils_py.exceptions import (
    DIDAlreadyExist,
)
from common_utils_py.metadata.exceptions import MetadataGenericError
from common_utils_py.metadata.metadata_provider import MetadataProvider
from common_utils_py.utils.utilities import checksum
from contracts_lib_py.utils import add_ethereum_prefix_and_hash_msg
from contracts_lib_py.web3_provider import Web3Provider
from eth_utils import add_0x_prefix

from nevermined_sdk_py.gateway.gateway_provider import GatewayProvider
from nevermined_sdk_py.secret_store.secret_store_provider import SecretStoreProvider

logger = logging.getLogger(__name__)


class Assets:
    """Nevermined assets class."""

    def __init__(self, keeper, did_resolver, agreements, asset_consumer, asset_executor, config):
        self._keeper = keeper
        self._did_resolver = did_resolver
        self._agreements = agreements
        self._asset_consumer = asset_consumer
        self._asset_executor = asset_executor
        self._config = config
        self._metadata_url = config.metadata_url

        downloads_path = os.path.join(os.getcwd(), 'downloads')
        if self._config.has_option('resources', 'downloads.path'):
            downloads_path = self._config.get('resources', 'downloads.path') or downloads_path
        self._downloads_path = downloads_path

    def _get_metadata_provider(self, url=None):
        return MetadataProvider.get_metadata_provider(url or self._metadata_url)

    def _get_secret_store(self, account):
        return SecretStoreProvider.get_secret_store(
            self._config.secret_store_url, self._config.parity_url, account
        )

    def create(self, metadata, publisher_account,
               service_descriptors=None, providers=None,
               authorization_type=ServiceAuthorizationTypes.PSK_RSA, use_secret_store=False,
               activity_id=None, attributes=None, asset_rewards={"_amounts": [], "_receivers": []},
               cap=None, royalties=None, mint=0):
        """
        Register an asset in both the keeper's DIDRegistry (on-chain) and in the Metadata store.

        :param metadata: dict conforming to the Metadata accepted by Nevermined Protocol.
        :param publisher_account: Account of the publisher registering this asset
        :param service_descriptors: list of ServiceDescriptor tuples of length 2.
            The first item must be one of ServiceTypes and the second
            item is a dict of parameters and values required by the service
        :param providers: list of addresses of providers of this asset (a provider is
            an ethereum account that is authorized to provide asset services)
        :param authorization_type: str indicate the authorization type that is going to be used
        to encrypt the urls.
            SecretStore, PSK-RSA and PSK-ECDSA are supported.
        :param use_secret_store: bool indicate whether to use the secret store directly for
            encrypting urls (Uses Gateway provider service if set to False)
        :param activity_id: identifier of the activity creating the new entity
        :param attributes: attributes associated with the action
        :param asset_rewards: rewards distribution including the amounts and the receivers
        :param cap: max cap of nfts that can be minted for the asset
        :param royalties: royalties in the secondary market going to the original creator
        :param mint: number of nfts to mint just after registration of the asset
        :return: DDO instance
        """
        assert isinstance(metadata, dict), f'Expected metadata of type dict, got {type(metadata)}'

        # copy metadata so we don't change the original
        metadata_copy = copy.deepcopy(metadata)

        # Create a DDO object
        ddo = DDO()
        gateway = GatewayProvider.get_gateway()
        ddo_service_endpoint = self._get_metadata_provider().get_service_endpoint()
        metadata_service_desc = ServiceDescriptor.metadata_service_descriptor(metadata_copy,
                                                                              ddo_service_endpoint)
        if metadata_copy['main']['type'] == 'dataset' or metadata_copy['main'][
            'type'] == 'algorithm':
            access_service_attributes = self._build_access(metadata_copy, publisher_account, asset_rewards)
            if not service_descriptors:
                if authorization_type == ServiceAuthorizationTypes.PSK_RSA:
                    service_descriptors = [ServiceDescriptor.authorization_service_descriptor(
                        self._build_authorization(authorization_type,
                                                  public_key=gateway.get_rsa_public_key(self._config)),
                        gateway.get_access_endpoint(self._config)
                    )]
                elif authorization_type == ServiceAuthorizationTypes.PSK_ECDSA:
                    service_descriptors = [ServiceDescriptor.authorization_service_descriptor(
                        self._build_authorization(authorization_type,
                                                  public_key=gateway.get_ecdsa_public_key(self._config)),
                        gateway.get_access_endpoint(self._config)
                    )]
                else:
                    service_descriptors = [ServiceDescriptor.authorization_service_descriptor(
                        self._build_authorization(authorization_type, threshold=0),
                        self._config.secret_store_url
                    )]
                service_descriptors += [ServiceDescriptor.access_service_descriptor(
                    access_service_attributes,
                    gateway.get_access_endpoint(self._config)
                )]
            else:
                service_types = set(map(lambda x: x[0], service_descriptors))
                if ServiceTypes.AUTHORIZATION not in service_types:
                    if authorization_type == ServiceAuthorizationTypes.PSK_RSA:
                        service_descriptors += [ServiceDescriptor.authorization_service_descriptor(
                            self._build_authorization(authorization_type,
                                                      public_key=gateway.get_rsa_public_key(self._config)),
                            gateway.get_access_endpoint(self._config)
                        )]
                    elif authorization_type == ServiceAuthorizationTypes.PSK_ECDSA:
                        service_descriptors += [ServiceDescriptor.authorization_service_descriptor(
                            self._build_authorization(authorization_type,
                                                      public_key=gateway.get_ecdsa_public_key(self._config)),
                            gateway.get_access_endpoint(self._config)
                        )]
                    else:
                        service_descriptors += [ServiceDescriptor.authorization_service_descriptor(
                            self._build_authorization(authorization_type, threshold=0),
                            self._config.secret_store_url
                        )]
                else:
                    service_descriptors += [ServiceDescriptor.access_service_descriptor(
                        access_service_attributes,
                        gateway.get_access_endpoint(self._config)

                    )]
        else:
            if not service_descriptors:
                service_descriptors = []
            else:
                service_descriptors += []
            logger.info('registering a workflow.')
        # Add all services to ddo
        service_descriptors = [metadata_service_desc] + service_descriptors

        services = ServiceFactory.build_services(service_descriptors)
        checksums = dict()
        for service in services:
            checksums[str(service.index)] = checksum(service.main)

        # Adding proof to the ddo.
        ddo.add_proof(checksums, publisher_account)

        # Generating the did and adding to the ddo.
        did_seed = checksum(ddo.proof['checksum'])
        asset_id = self._keeper.did_registry.hash_did(did_seed, publisher_account.address)
        ddo._did = DID.did(asset_id)
        did = ddo._did

        logger.debug(f'Generating new did: {did}')
        # Check if it's already registered first!
        if did in self._get_metadata_provider().list_assets():
            raise DIDAlreadyExist(
                f'Asset id {did} is already registered to another asset.')

        for service in services:
            if service.type == ServiceTypes.ASSET_ACCESS:
                access_service = ServiceFactory.complete_access_service(
                    did,
                    gateway.get_access_endpoint(self._config),
                    access_service_attributes,
                    self._keeper.access_template.address,
                    self._keeper.escrow_payment_condition.address,
                    service.type
                )
                ddo.add_service(access_service)
            elif service.type == ServiceTypes.NFT_ACCESS:
                access_service = ServiceFactory.complete_access_service(
                    did,
                    gateway.get_nft_access_endpoint(self._config),
                    self._build_nft_access(metadata_copy, publisher_account, asset_rewards, service.main['_numberNfts']),
                    self._keeper.nft_access_template.address,
                    self._keeper.escrow_payment_condition.address,
                    service.type
                )
                ddo.add_service(access_service)
            elif service.type == ServiceTypes.NFT_SALES:
                nft_sales_service = ServiceFactory.complete_nft_sales_service(
                    did,
                    gateway.get_access_endpoint(self._config),
                    service.attributes,
                    self._keeper.nft_sales_template.address,
                    self._keeper.escrow_payment_condition.address,
                    service.type
                )
                ddo.add_service(nft_sales_service)
            elif service.type == ServiceTypes.METADATA:
                ddo_service_endpoint = service.service_endpoint.replace('{did}', did)
                service.set_service_endpoint(ddo_service_endpoint)
                ddo.add_service(service)
            elif service.type == ServiceTypes.CLOUD_COMPUTE:
                compute_service = ServiceFactory.complete_compute_service(
                    did,
                    service.service_endpoint,
                    service.attributes,
                    self._keeper.compute_execution_condition.address,
                    self._keeper.escrow_payment_condition.address
                )
                ddo.add_service(compute_service)
            else:
                ddo.add_service(service)

        ddo.proof['signatureValue'] = self._keeper.sign_hash(
            add_ethereum_prefix_and_hash_msg(did_to_id_bytes(did)),
            publisher_account)

        # Add public key and authentication
        ddo.add_public_key(did, publisher_account.address)

        ddo.add_authentication(did, PUBLIC_KEY_TYPE_RSA)

        # Setup metadata service
        # First compute files_encrypted
        if metadata_copy['main']['type'] in ['dataset', 'algorithm']:
            assert metadata_copy['main'][
                'files'], 'files is required in the metadata main attributes.'
            logger.debug('Encrypting content urls in the metadata.')
            if not use_secret_store:
                encrypt_endpoint = gateway.get_encrypt_endpoint(self._config)
                files_encrypted = gateway.encrypt_files_dict(
                    metadata_copy['main']['files'],
                    encrypt_endpoint,
                    ddo.asset_id,
                    authorization_type)
            else:
                files_encrypted = self._get_secret_store(publisher_account) \
                    .encrypt_document(
                    did_to_id(did),
                    json.dumps(metadata_copy['main']['files']),
                )
            # only assign if the encryption worked
            if files_encrypted:
                logger.debug(f'Content urls encrypted successfully {files_encrypted}')
                index = 0
                for file in metadata_copy['main']['files']:
                    file['index'] = index
                    index = index + 1
                    del file['url']
                metadata_copy['encryptedFiles'] = files_encrypted
            else:
                raise AssertionError('Encrypting the files failed.')

        # DDO url and `Metadata` service

        logger.debug(
            f'Generated ddo and services, DID is {ddo.did},'
            f' metadata service @{ddo_service_endpoint}.')
        response = None

        # register on-chain
        if mint > 0 or royalties is not None or cap is not None:
            registered_on_chain = self._keeper.did_registry.register_mintable_did(
                did_seed,
                checksum=Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
                url=ddo_service_endpoint,
                account=publisher_account,
                cap=cap,
                royalties=royalties,
                providers=providers,
                activity_id=activity_id,
                attributes=attributes
            )
            if mint > 0:
                self._keeper.did_registry.mint(ddo.asset_id, mint, account=publisher_account)
        else:
            registered_on_chain = self._keeper.did_registry.register(
                did_seed,
                checksum=Web3Provider.get_web3().toBytes(hexstr=ddo.asset_id),
                url=ddo_service_endpoint,
                account=publisher_account,
                cap=cap,
                royalties=royalties,
                providers=providers,
                activity_id=activity_id,
                attributes=attributes
            )

        if registered_on_chain is False:
            logger.warning(f'Registering {did} on-chain failed.')
            return None
        logger.info(f'Successfully registered DDO (DID={did}) on chain.')
        try:
            # publish the new ddo
            response = self._get_metadata_provider().publish_asset_ddo(ddo)
            logger.info('Asset/ddo published successfully in Metadata.')
        except ValueError as ve:
            raise ValueError(f'Invalid value to publish in the metadata: {str(ve)}')
        except Exception as e:
            logger.error(f'Publish asset in Metadata failed: {str(e)}')
        if not response:
            return None
        return ddo

    def create_compute(self, metadata, publisher_account, asset_rewards={"_amounts": [], "_receivers": []},
                       service_descriptors=None, providers=None,
                       authorization_type=ServiceAuthorizationTypes.PSK_RSA, use_secret_store=False):
        """
        Register a compute to the data asset in both the keeper's DIDRegistry (on-chain) and in
        the Metadata store.

        :param metadata: dict conforming to the Metadata accepted by Nevermined Protocol.
        :param publisher_account: Account of the publisher registering this asset
        :param asset_rewards: Asset rewards distribution including amounts and receivers
        :param service_descriptors: list of ServiceDescriptor tuples of length 2.
            The first item must be one of ServiceTypes and the second
            item is a dict of parameters and values required by the service
        :param providers: list of addresses of providers of this asset (a provider is
            an ethereum account that is authorized to provide asset services)
        :param authorization_type: str indicate the authorization type that is going to be used
        to encrypt the urls.
            SecretStore, PSK-RSA and PSK-ECDSA are supported.
        :param use_secret_store: bool indicate whether to use the secret store directly for
            encrypting urls (Uses Gateway provider service if set to False)
        :return: DDO instance
        """

        metadata_copy = copy.deepcopy(metadata)
        gateway = GatewayProvider.get_gateway()

        compute_service_attributes = self._build_compute(metadata_copy, publisher_account, asset_rewards)
        service_descriptor = ServiceDescriptor.compute_service_descriptor(
            compute_service_attributes, gateway.get_execute_endpoint(self._config))

        return self.create(metadata, publisher_account, service_descriptors=[service_descriptor],
                           providers=providers, authorization_type=authorization_type,
                           use_secret_store=use_secret_store)

    def retire(self, did):
        """
        Retire this did of Metadata

        :param did: DID, str
        :return: bool
        """
        try:
            ddo = self.resolve(did)
            metadata_service = ddo.get_service(ServiceTypes.METADATA)
            self._get_metadata_provider(metadata_service.service_endpoint).retire_asset_ddo(did)
            return True
        except MetadataGenericError as err:
            logger.error(err)
            return False

    def resolve(self, did):
        """
        When you pass a did retrieve the ddo associated.

        :param did: DID, str
        :return: DDO instance
        """
        return self._did_resolver.resolve(did)

    def search(self, text, sort=None, offset=100, page=1, metadata_url=None):
        """
        Search an asset in oceanDB using Metadata.

        :param text: String with the value that you are searching
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param metadata_url: Url of the Metadata where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query
        """
        assert page >= 1, f'Invalid page value {page}. Required page >= 1.'
        logger.info(f'Searching asset containing: {text}')
        return [DDO(dictionary=ddo_dict) for ddo_dict in
                self._get_metadata_provider(metadata_url).text_search(text, sort, offset, page)[
                    'results']]

    def query(self, query, sort=None, offset=100, page=1, metadata_url=None):
        """
        Search an asset in oceanDB using search query.

        :param query: dict with query parameters
            (e.g.) https://github.com/nevermined-io/metadata-api/blob/develop/docs
            /for_api_users/API.md
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param metadata_url: Url of the Metadata where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query.
        """
        logger.info(f'Searching asset query: {query}')
        metadata_provider = self._get_metadata_provider(metadata_url)
        return [DDO(dictionary=ddo_dict) for ddo_dict in
                metadata_provider.query_search(query, sort, offset, page)['results']]

    def order(self, did, index, consumer_account, account):
        agreement_id = ServiceAgreement.create_new_agreement_id()
        logger.debug(f'about to request create agreement: {agreement_id}')
        self._agreements.create(
            did,
            index,
            agreement_id,
            consumer_account.address,
            account
        )
        return agreement_id

    def access(self, service_agreement_id, did, service_index, consumer_account,
               destination, index=None, service_type=ServiceTypes.ASSET_ACCESS):
        """
        Consume the asset data.

        Using the service endpoint defined in the ddo's service pointed to by service_definition_id.
        Consumer's permissions is checked implicitly by the secret-store during decryption
        of the contentUrls.
        The service endpoint is expected to also verify the consumer's permissions to access this
        asset.
        This method downloads and saves the asset datafiles to disk.

        :param service_type:
        :param service_agreement_id: str
        :param did: DID, str
        :param service_index: identifier of the service inside the asset DDO, str
        :param consumer_account: Account instance of the consumer
        :param destination: str path
        :param index: Index of the document that is going to be downloaded, int
        :return: str path to saved files
        """
        ddo = self.resolve(did)
        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
        return self._asset_consumer.access(
            service_agreement_id,
            service_index,
            ddo,
            consumer_account,
            destination,
            GatewayProvider.get_gateway(),
            self._get_secret_store(consumer_account),
            self._config,
            index,
            service_type=service_type
        )

    def download(self, did, service_index, owner_account, destination, index=None):
        """
        Download the asset data.

        Using the service endpoint defined in the ddo's service pointed to by service_definition_id.
        Consumer's permissions is checked implicitly by the secret-store during decryption
        of the contentUrls.
        The service endpoint is expected to also verify that `owner_account` is the actual owner
        of the asset.
        This method downloads and saves the asset datafiles to disk.

        :param did: DID, str
        :param service_index: identifier of the service inside the asset DDO, str
        :param owner_account: Account instance of the owner
        :param destination: str path
        :param index: Index of the document that is going to be downloaded, int
        :return: str path to saved files
        """
        ddo = self.resolve(did)
        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
        return self._asset_consumer.download(
            service_index,
            ddo,
            owner_account,
            destination,
            GatewayProvider.get_gateway(),
            self._get_secret_store(owner_account),
            self._config,
            index
        )

    def compute_logs(self, service_agreement_id, execution_id, account):
        """
        Get the logs of a compute workflow.

        :param service_agreement_id: The id of the service agreement that ordered the compute job, str
        :param execution_id: The id of the compute job, str
        :param account: Account instance that ordered the execution of the compute job
        :return: list, compute logs
        """
        return self._asset_consumer.compute_logs(
            service_agreement_id,
            execution_id,
            account,
            GatewayProvider.get_gateway(),
            self._config,
        )

    def compute_status(self, service_agreement_id, execution_id, account):
        """
        Get the status of a compute workflow.

        :param service_agreement_id: The id of the service agreement that ordered the compute job, str
        :param execution_id: The id of the compute job, str
        :param account: Account instance that ordered the execution of the compute job
        :return: str compute status
        """
        return self._asset_consumer.compute_status(
            service_agreement_id,
            execution_id,
            account,
            GatewayProvider.get_gateway(),
            self._config,
        )

    def owner(self, did):
        """
        Return the owner of the asset.

        :param did: DID, str
        :return: the ethereum address of the owner/publisher of given asset did, hex-str
        """
        # return self._get_metadata_provider(self._metadata_url).get_asset_ddo(did).proof['creator']
        return self._keeper.did_registry.get_did_owner(did_to_id(did))

    def owner_assets(self, owner_address):
        """
        List of Asset objects published by ownerAddress

        :param owner_address: ethereum address of owner/publisher, hex-str
        :return: list of dids
        """
        return self._keeper.did_registry.get_owner_asset_ids(owner_address)

    def consumer_assets(self, consumer_address):
        """
        List of Asset objects purchased by consumerAddress

        :param consumer_address: ethereum address of consumer, hes-str
        :return: list of dids
        """
        return self._keeper.access_condition.get_purchased_assets_by_address(
            consumer_address)

    def revoke_permissions(self, did, address_to_revoke, account):
        """
        Revoke access permission to an address.

        :param did: the id of an asset on-chain, hex str
        :param address_to_revoke: ethereum account address, hex str
        :param account: Account executing the action
        :return: bool
        """
        asset_id = add_0x_prefix(did_to_id(did))
        return self._keeper.did_registry.revoke_permission(asset_id, address_to_revoke, account)

    def get_permissions(self, did, address):
        """
        Gets access permission of a grantee

        :param did: the id of an asset on-chain, hex str
        :param address: ethereum account address, hex str
        :return: true if the address has access permission to a DID
        """
        asset_id = add_0x_prefix(did_to_id(did))
        return self._keeper.did_registry.get_permission(asset_id, address)

    def delegate_persmission(self, did, address_to_grant, account):
        """
        Grant access permission to an address.

        :param did: the id of an asset on-chain, hex str
        :param address_to_grant: ethereum account address, hex str
        :param account: Account executing the action
        :return: bool
        """
        asset_id = add_0x_prefix(did_to_id(did))
        return self._keeper.did_registry.grant_permission(asset_id, address_to_grant, account)

    def transfer_ownership(self, did, new_owner_address, account):
        """
        Transfer did ownership to an address.

        :param did: the id of an asset on-chain, hex str
        :param new_owner_address: ethereum account address, hex str
        :param account: Account executing the action
        :return: bool
        """
        asset_id = add_0x_prefix(did_to_id(did))
        return self._keeper.did_registry.transfer_did_ownership(asset_id, new_owner_address,
                                                                account)

    def execute(self, agreement_id, did, index, consumer_account, workflow_did):
        """

        :param agreement_id:representation of `bytes32` id, hexstr
        :param did: computing service did, str
        :param index: id of the service within the asset DDO, str
        :param consumer_account: Account instance of the consumer ordering the service
        :param workflow_did: the asset did (of `workflow` type) which consist of `did:nv:` and
        the assetId hex str (without `0x` prefix), str
        :return: the id of the compute job, str
        """
        workflow_ddo = self.resolve(workflow_did)
        compute_ddo = self.resolve(did)
        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')
        return self._asset_executor.execute(
            agreement_id,
            compute_ddo,
            workflow_ddo,
            consumer_account,
            GatewayProvider.get_gateway(),
            index,
            self._config
        )

    @staticmethod
    def _build_authorization(authorization_type, public_key=None, threshold=None):
        authorization = dict()
        authorization['main'] = dict()
        authorization['main']['service'] = authorization_type
        if public_key:
            authorization['main']['publicKey'] = public_key
        if threshold:
            authorization['main']['threshold'] = threshold
        return authorization

    @staticmethod
    def _build_access(metadata, publisher_account, asset_rewards):
        return {"main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": publisher_account.address,
            "price": metadata[MetadataMain.KEY]['price'],
            "timeout": 3600,
            "datePublished": metadata[MetadataMain.KEY]['dateCreated'],
            "_amounts": asset_rewards["_amounts"],
            "_receivers": asset_rewards["_receivers"]
        }}

    @staticmethod
    def _build_nft_access(metadata, publisher_account, asset_rewards, number_nfts):
        return {"main": {
            "name": "nftAccessAgreement",
            "creator": publisher_account.address,
            "price": metadata[MetadataMain.KEY]['price'],
            "timeout": 3600,
            "datePublished": metadata[MetadataMain.KEY]['dateCreated'],
            "_amounts": asset_rewards["_amounts"],
            "_receivers": asset_rewards["_receivers"],
            "_numberNfts": number_nfts
        }}

    def _build_compute(self, metadata, publisher_account, asset_rewards):
        return {"main": {
            "name": "dataAssetComputeServiceAgreement",
            "creator": publisher_account.address,
            "datePublished": metadata[MetadataMain.KEY]['dateCreated'],
            "price": metadata[MetadataMain.KEY]['price'],
            "timeout": 86400,
            "provider": self._build_provider_config(),
            "_amounts": asset_rewards["_amounts"],
            "_receivers": asset_rewards["_receivers"]
        }
        }

    @staticmethod
    def _build_provider_config():
        # TODO manage this as different class and get all the info for different services
        return {
            "type": "Azure",
            "description": "",
            "environment": {
                "cluster": {
                    "type": "Kubernetes",
                    "url": "http://10.0.0.17/xxx"
                },
                "supportedContainers": [
                    {
                        "image": "tensorflow/tensorflow",
                        "tag": "latest",
                        "checksum":
                            "sha256:cb57ecfa6ebbefd8ffc7f75c0f00e57a7fa739578a429b6f72a0df19315deadc"
                    },
                    {
                        "image": "tensorflow/tensorflow",
                        "tag": "latest",
                        "checksum":
                            "sha256:cb57ecfa6ebbefd8ffc7f75c0f00e57a7fa739578a429b6f72a0df19315deadc"
                    }
                ],
                "supportedServers": [
                    {
                        "serverId": "1",
                        "serverType": "xlsize",
                        "price": "50",
                        "cpu": "16",
                        "gpu": "0",
                        "memory": "128gb",
                        "disk": "160gb",
                        "maxExecutionTime": 86400
                    },
                    {
                        "serverId": "2",
                        "serverType": "medium",
                        "price": "10",
                        "cpu": "2",
                        "gpu": "0",
                        "memory": "8gb",
                        "disk": "80gb",
                        "maxExecutionTime": 86400
                    }
                ]
            }
        }
