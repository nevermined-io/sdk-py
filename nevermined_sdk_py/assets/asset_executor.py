import logging

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes

logger = logging.getLogger(__name__)


class AssetExecutor:
    """Class representing the call to the Gateway execute endpoint."""

    @staticmethod
    def execute(agreement_id, compute_ddo, workflow_ddo, consumer_account, gateway, index, config):
        """

        :param agreement_id:
        :param workflow_ddo:
        :param consumer_account:
        :param index:
        :return: the id of the compute job
        """
        service_endpoint = ServiceAgreement.from_ddo(ServiceTypes.CLOUD_COMPUTE,
                                                     compute_ddo).service_endpoint
        response = gateway.execute_compute_service(agreement_id, service_endpoint,
                                                   consumer_account, workflow_ddo, config)

        return response.json()["workflowId"]
