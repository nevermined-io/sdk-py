#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0


def test_create_access_service(publisher_ocean_instance):
    service = publisher_ocean_instance.services.create_access_service(1, 'service_endpoint')
    assert service[0] == 'access'
    assert service[1]['attributes'] == 1
    assert service[1]['serviceEndpoint'] == 'service_endpoint'
