#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os

import pytest


def unit_test(test):
    """
    Mark all test (suites) with this decorator that test isolated functions classes optionally
    with mocked out dependencies.
    Unit tests should live next to the file there testing with a *_test.py suffix,
    e.g. `foo_test.py` next to `foo.py`.
    """

    return test  # Always run all unit tests for now


def integration_test(test):
    """
    Mark all test (suites) with this decorator that test interactions between multiple classes,
    but don't touch external services.
    Integration tests should live in the `squid_py/test/integration` folder and
    `squid_py/<package>/test` folders of individual sub-packages.
    """

    return pytest.mark.skip(reason='Integration tests not enabled')(test) if not should_run_test(
        'integration') else test


def e2e_test(test):
    """
    Mark all test (suites) with this decorator that test interactions between multiple classes
    and external services.
    End-to-end tests should live in the `squid_py/test/e2e` and `squid_py/examples` folders.
    """

    return pytest.mark.skip(reason='End to end tests not enabled')(test) if not should_run_test(
        'e2e') else test


def should_run_test(test_tier, active_tier=None):
    tiers = ['unit', 'integration', 'e2e']
    active_tier_index = tiers.index(active_tier or _get_active_test_tier())
    test_tier_index = tiers.index(test_tier)
    return test_tier_index <= active_tier_index


def _get_active_test_tier():
    return os.getenv('TEST_TIER', 'e2e')
