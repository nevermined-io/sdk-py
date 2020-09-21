import os

from requests import Response

from nevermined_sdk_py.gateway.gateway import Gateway


class GatewayMock(object):
    def __init__(self, ocean_instance=None, account=None):
        if not ocean_instance:
            from tests.resources.helper_functions import get_publisher_instance
            ocean_instance = get_publisher_instance(
                init_tokens=False, use_ss_mock=False, use_gateway_mock=True
            )

        self.ocean_instance = ocean_instance
        self.account = account
        if not account:
            from tests.resources.helper_functions import get_publisher_account
            self.account = get_publisher_account()

        # nevermined_instance.agreements.watch_provider_events(self.account)

    @staticmethod
    def consume_service(did, service_agreement_id, service_endpoint, account_address, files,
                        destination_folder, *_, **__):
        for f in files:
            with open(os.path.join(destination_folder, os.path.basename(f['url'])), 'w') as of:
                of.write(f'mock data {service_agreement_id}.{service_endpoint}.{account_address}')

    @staticmethod
    def access_service(did, service_agreement_id, service_endpoint, account, destination_folder,
                       index, *_, **__):
        with open(os.path.join(destination_folder, os.path.basename(did)), 'w') as of:
            of.write(f'mock data {service_agreement_id}.{service_endpoint}.{account}')

    @staticmethod
    def encrypt_files_dict(files_dict, encrypt_endpoint, asset_id, method):
        encrypted = f'{method}.{asset_id}!!{files_dict}!!'
        return encrypted

    @staticmethod
    def execute_service(agreement_id, service_endpoint, consumer_account, workflow_ddo):
        return True

    @staticmethod
    def execute_compute_service(agreement_id, service_endpoint, consumer_account, workflow_ddo):
        r = Response()
        r._content = b'{"workflowId": "nevermined-compute-h4trr"}'
        return r

    @staticmethod
    def get_gateway_url(config):
        return Gateway.get_gateway_url(config)

    @staticmethod
    def get_access_endpoint(config):
        return f'{Gateway.get_gateway_url(config)}/services/access'

    @staticmethod
    def get_consume_endpoint(config):
        return f'{Gateway.get_gateway_url(config)}/services/consume'

    @staticmethod
    def get_execute_endpoint(config):
        return f'{Gateway.get_gateway_url(config)}/services/execute'

    @staticmethod
    def get_encrypt_endpoint(config):
        return f'{Gateway.get_gateway_url(config)}/services/encrypt'

    @staticmethod
    def get_rsa_public_key(config):
        return 'rsa_public_key'

    @staticmethod
    def get_ecdsa_public_key(config):
        return 'ecdsa-public-key'
