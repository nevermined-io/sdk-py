"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from common_utils_py.agreements.service_factory import ServiceDescriptor


class OceanServices:
    """Ocean services class."""

    @staticmethod
    def create_access_service(attributes, service_endpoint):
        """
        Publish an asset with an `Access` service according to the supplied attributes.

        :param attributes: attributes of the access service, dict
        :param service_endpoint: str URL for initiating service access request
        :return: Service instance or None
        """
        service = ServiceDescriptor.access_service_descriptor(attributes, service_endpoint)
        return service
