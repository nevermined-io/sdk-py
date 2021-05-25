import logging
from nevermined_sdk_py.nevermined.files import Files

from common_utils_py.did_resolver.did_resolver import DIDResolver
from contracts_lib_py.contract_handler import ContractHandler
from contracts_lib_py.web3_provider import Web3Provider

from nevermined_sdk_py.assets.asset_consumer import AssetConsumer
from nevermined_sdk_py.assets.asset_executor import AssetExecutor
from nevermined_sdk_py.config_provider import ConfigProvider
from nevermined_sdk_py.faucet.faucet import Faucet
from nevermined_sdk_py.nevermined.accounts import Accounts
from nevermined_sdk_py.nevermined.agreements import Agreements
from nevermined_sdk_py.nevermined.assets import Assets
from nevermined_sdk_py.nevermined.auth import Auth
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from nevermined_sdk_py.nevermined.nfts import NFTs
from nevermined_sdk_py.nevermined.provenance import Provenance
from nevermined_sdk_py.nevermined.providers import Providers
from nevermined_sdk_py.nevermined.secret_store import SecretStore
from nevermined_sdk_py.nevermined.services import Services
from nevermined_sdk_py.nevermined.templates import Templates
from nevermined_sdk_py.nevermined.tokens import Tokens

CONFIG_FILE_ENVIRONMENT_NAME = 'CONFIG_FILE'

logger = logging.getLogger(__name__)


class Nevermined:
    """The Nevermined class is the entry point into Nevermined Protocol."""

    def __init__(self, config=None):
        """
        Initialize Nevermined class.
           >> # Make a new Nevermined instance
           >> nevermined = Nevermined({...})

        This class provides the main top-level functions in nevermined protocol:
         * Publish assets metadata and associated services
            * Each asset is assigned a unique DID and a DID Document (DDO)
            * The DDO contains the asset's services including the metadata
            * The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            >> ddo = nevermined.assets.create(metadata, publisher_account)

         * Discover/Search assets via the current configured metadata store.
            >> assets_list = nevermined.assets.search('search text')

         * Purchase asset services by choosing a service agreement from the
           asset's DDO. Purchase goes through the service agreements interface
           and starts by signing a service agreement then sending the signature
           to the publisher's Gateway server via the `purchaseEndpoint` in the service
           definition:

           >> service_def_id = ddo.get_service(ServiceTypes.ASSET_ACCESS).service_definition_id
           >> service_agreement_id = nevermined.assets.order(did, service_def_id, consumer_account)

        An instance of Nevermined is parameterized by a `Config` instance.

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
            'NeverminedToken',
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
        self.tokens = Tokens(self._keeper)
        self.accounts = Accounts(self._keeper, self._config, self.tokens, Faucet)
        self.templates = Templates(
            self._keeper,
            config
        )
        self.agreements = self._make_agreements()
        self.assets = Assets(
            self._keeper,
            self._did_resolver,
            self.agreements,
            AssetConsumer,
            AssetExecutor,
            self._config
        )
        self.nfts = NFTs(self._keeper)
        self.services = Services()
        self.secret_store = SecretStore(self._config)
        self.providers = Providers(self._keeper, self._did_resolver, self._config)
        self.auth = Auth(self._keeper, self._config.storage_path)
        self.provenance = Provenance(self._keeper, self._config)
        self.files = Files(self._config)

        logger.debug('Nevermined instance initialized: ')
        logger.debug(f'\tOther accounts: {sorted([a.address for a in self.accounts.list()])}')
        logger.debug(f'\tDIDRegistry @ {self._keeper.did_registry.address}')

    @property
    def config(self):
        return self._config

    @property
    def keeper(self):
        """Keeper instance."""
        return self._keeper

    def _make_agreements(self):
        return Agreements(
            self._keeper,
            self._did_resolver,
            AssetConsumer,
            AssetExecutor,
            self._config
        )
