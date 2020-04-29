class ConfigProvider:
    """Provides the Config instance."""
    _config = None

    @staticmethod
    def get_config():
        """ Get a Config instance."""
        assert ConfigProvider._config, 'set_config first.'
        return ConfigProvider._config

    @staticmethod
    def set_config(config):
        """
         Set a Config instance.

        :param config: Config
        :return:  New Config instance.
        """
        ConfigProvider._config = config
