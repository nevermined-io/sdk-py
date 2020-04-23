class OceanProviders:
    """Ocean assets class."""

    def __init__(self, keeper, did_resolver, config):
        self._keeper = keeper
        self._did_resolver = did_resolver
        self._config = config

    def add(self, did, provider_address, account):
        return self._keeper.did_registry.add_provider(did, provider_address, account)

    def remove(self, did, provider_address, account):
        return self._keeper.did_registry.remove_provider(did, provider_address, account)

    def list(self, did):
        return self._keeper.did_registry.get_did_providers(did)
