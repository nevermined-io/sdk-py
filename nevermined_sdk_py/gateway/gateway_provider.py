from nevermined_sdk_py.gateway.gateway import Gateway


class GatewayProvider(object):
    """Provides a Gateway instance."""
    _gateway_class = Gateway

    @staticmethod
    def get_gateway():
        """ Get a Gateway instance."""
        return GatewayProvider._gateway_class()

    @staticmethod
    def set_gateway_class(gateway_class):
        """
         Set a Gateway class.

        :param gateway_class: Gateway-compatible class
        """
        GatewayProvider._gateway_class = gateway_class
