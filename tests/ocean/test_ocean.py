"""Test ocean class."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from tests.resources.tiers import e2e_test


@e2e_test
def test_ocean_instance(publisher_ocean_instance):
    assert publisher_ocean_instance.tokens
    assert publisher_ocean_instance.agreements
    assert publisher_ocean_instance.assets
    assert publisher_ocean_instance.accounts
    assert publisher_ocean_instance.services
    assert publisher_ocean_instance.auth
    assert publisher_ocean_instance.templates
    assert publisher_ocean_instance.secret_store
