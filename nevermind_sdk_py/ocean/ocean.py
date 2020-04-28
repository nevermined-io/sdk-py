import logging

from deprecated import deprecated
from contracts_lib_py.contract_handler import ContractHandler
from contracts_lib_py.web3_provider import Web3Provider
from common_utils_py.did_resolver.did_resolver import DIDResolver

from nevermind_sdk_py.assets.asset_consumer import AssetConsumer
from nevermind_sdk_py.assets.asset_executor import AssetExecutor
from nevermind_sdk_py.config_provider import ConfigProvider
from nevermind_sdk_py.ocean.keeper import SquidKeeper as Keeper
from nevermind_sdk_py.ocean.ocean_accounts import OceanAccounts
from nevermind_sdk_py.ocean.ocean_agreements import OceanAgreements
from nevermind_sdk_py.ocean.ocean_assets import OceanAssets
from nevermind_sdk_py.ocean.ocean_auth import OceanAuth
from nevermind_sdk_py.ocean.ocean_providers import OceanProviders
from nevermind_sdk_py.ocean.ocean_secret_store import OceanSecretStore
from nevermind_sdk_py.ocean.ocean_services import OceanServices
from nevermind_sdk_py.ocean.ocean_templates import OceanTemplates
from nevermind_sdk_py.ocean.ocean_tokens import OceanTokens

CONFIG_FILE_ENVIRONMENT_NAME = 'CONFIG_FILE'

logger = logging.getLogger('ocean')

class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    def __init__(self, config=None):
        """
        Initialize Ocean class.
           >> # Make a new Ocean instance
           >> ocean = Ocean({...})

        This class provides the main top-level functions in ocean protocol:
         * Publish assets metadata and associated services
            * Each asset is assigned a unique DID and a DID Document (DDO)
            * The DDO contains the asset's services including the metadata
            * The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            >> ddo = ocean.assets.create(metadata, publisher_account)

         * Discover/Search assets via the current configured metadata store (Aquarius)
            >> assets_list = ocean.assets.search('search text')

         * Purchase asset services by choosing a service agreement from the
           asset's DDO. Purchase goes through the service agreements interface
           and starts by signing a service agreement then sending the signature
           to the publisher's Brizo server via the `purchaseEndpoint` in the service
           definition:

           >> service_def_id = ddo.get_service(ServiceTypes.ASSET_ACCESS).service_definition_id
           >> service_agreement_id = ocean.assets.order(did, service_def_id, consumer_account)

        An instance of Ocean is parameterized by a `Config` instance.

        :param config: Config instance
        """
        # Configuration information for the market is stored in the Config class
        # config = Config(filename=config_file, options_dict=config_dict)
        if not config:
            config = ConfigProvider.get_config()

        self._config = config
        self._web3 = Web3Provider.get_web3(self._config.keeper_url)
        ContractHandler.artifacts_path = self._config.keeper_path
        contracts = [
            'DIDRegistry',
            'Dispenser',
            'TemplateStoreManager',
            'OceanToken',
            'ConditionStoreManager',
            'EscrowAccessSecretStoreTemplate',
            'AgreementStoreManager',
            'AgreementStoreManager',
            'AccessSecretStoreCondition',
            'LockRewardCondition',
            'HashLockCondition',
            'SignCondition',
            'EscrowReward'
        ]
        self._keeper = Keeper.get_instance(self._config.keeper_path, contracts)
        self._did_resolver = DIDResolver(self._keeper.did_registry)

        # Initialize the public sub-modules
        self.tokens = OceanTokens(self._keeper)
        self.accounts = OceanAccounts(self._keeper, self._config, self.tokens)
        self.secret_store = OceanSecretStore(self._config)
        self.templates = OceanTemplates(
            self._keeper,
            config
        )
        self.agreements = self._make_ocean_agreements()
        self.assets = OceanAssets(
            self._keeper,
            self._did_resolver,
            self.agreements,
            AssetConsumer,
            AssetExecutor,
            self._config
        )
        self.services = OceanServices()
        self.ocean_providers = OceanProviders(self._keeper, self._did_resolver, self._config)
        self.auth = OceanAuth(self._keeper, self._config.storage_path)

        logger.debug('Squid Ocean instance initialized: ')
        logger.debug(f'\tOther accounts: {sorted([a.address for a in self.accounts.list()])}')
        logger.debug(f'\tDIDRegistry @ {self._keeper.did_registry.address}')

    @property
    def config(self):
        return self._config

    @property
    def keeper(self):
        """Keeper instance."""
        return self._keeper

    def _make_ocean_agreements(self):
        return OceanAgreements(
            self._keeper,
            self._did_resolver,
            AssetConsumer,
            AssetExecutor,
            self._config
        )

    @deprecated("Use ocean.accounts.list")
    def get_accounts(self):
        """
        Returns all available accounts loaded via a wallet, or by Web3.

        :return: list of Account instances
        """
        return self.accounts.list()

    @deprecated("Use ocean.assets.search")
    def search_assets_by_text(self, *args, **kwargs):
        """
        Search an asset in oceanDB using metadata.

        see OceanAssets.search for params

        :return: List of assets that match with the query
        """
        return self.assets.search(*args, **kwargs)['results']

    @deprecated("Use ocean.assets.query")
    def search_assets(self, *args, **kwargs):
        """
        Search an asset in oceanDB using search query.

        See OceanAssets.query for params

        :return: List of assets that match with the query.
        """
        return self.assets.query(*args, **kwargs)

    @deprecated("Use ocean.assets.create")
    def register_asset(self, *args, **kwargs):
        """
        Register an asset in both the keeper's DIDRegistry (on-chain) and in the Metadata store (
        Aquarius).

        See OceanAssets.query for params

        :return: DDO instance
        """
        return self.assets.create(*args, **kwargs)

    @deprecated("Use ocean.assets.order")
    def purchase_asset_service(self, *args, **kwargs):
        """
        Sign service agreement.

        Sign the service agreement defined in the service section identified
        by `service_definition_id` in the ddo and send the signed agreement to the purchase endpoint
        associated with this service.

        :return: tuple(agreement_id, signature) the service agreement id (can be used to query
            the keeper-contracts for the status of the service agreement) and signed agreement hash
        """
        return self.assets.order(*args, **kwargs)

    @deprecated("Use ")
    def execute_service_agreement(self, *args, **kwargs):
        """
        Execute the service agreement on-chain using keeper's ServiceExecutionAgreement contract.

        The on-chain initializeAgreement method requires the following arguments:
        templateId, signature, consumer, hashes, timeouts, serviceAgreementId, did.
        `agreement_message_hash` is necessary to verify the signature.
        The consumer `signature` includes the conditions timeouts and parameters values which
        is usedon-chain to verify that the values actually match the signed hashes.

        :return: dict the `initializeAgreement` transaction receipt
        """
        return self.agreements.create(*args, **kwargs)

    @deprecated("Use ")
    def is_access_granted(self, *args, **kwargs):
        """
        Check permission for the agreement.

        Verify on-chain that the `consumer_address` has permission to access the given asset `did`
        according to the `service_agreement_id`.

        :return: bool True if user has permission
        """
        return self.agreements.is_access_granted(*args, **kwargs)

    @deprecated("Use ocean.assets.resolve")
    def resolve_asset_did(self, did):
        """
        When you pass a did retrieve the ddo associated.

        :param did: DID, str
        :return: DDO
        """
        return self.assets.resolve(did)

    @deprecated("Use ocean.assets.consume")
    def consume_service(self, *args, **kwargs):
        """
        Consume the asset data.

        Using the service endpoint defined in the ddo's service pointed to by service_definition_id.
        Consumer's permissions is checked implicitly by the secret-store during decryption
        of the contentUrls.
        The service endpoint is expected to also verify the consumer's permissions to consume this
        asset.
        This method downloads and saves the asset datafiles to disk.

        :return: None
        """
        return self.assets.consume(*args, **kwargs)
