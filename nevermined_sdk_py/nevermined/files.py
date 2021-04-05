from nevermined_sdk_py.gateway.gateway import Gateway
import pathlib

from nevermined_sdk_py.gateway.gateway_provider import GatewayProvider


class Files:
    """Nevermined Files class."""

    def __init__(self, config):
        self._config = config

    def upload_filecoin(self, file_path):
        """Upload a file to Filecoin

        param file_path: The path to the file to upload, str
        return: The url with the cid, str
        """
        path = pathlib.Path(file_path)
        if not path.is_file():
            raise ValueError(f'File {file_path} not found or not a file')

        with path.open('rb') as f:
            gateway = GatewayProvider.get_gateway()
            response =  gateway.upload_filecoin(f, self._config)
            return response['url']