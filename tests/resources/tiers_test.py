#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from .tiers import should_run_test


def test_unit_tier():
    assert should_run_test('unit', 'unit') is True
    assert should_run_test('integration', 'unit') is False
    assert should_run_test('e2e', 'unit') is False


def test_integration_tier():
    assert should_run_test('unit', 'integration') is True
    assert should_run_test('integration', 'integration') is True
    assert should_run_test('e2e', 'integration') is False


def test_e2e_tier():
    assert should_run_test('unit', 'e2e') is True
    assert should_run_test('integration', 'e2e') is True
    assert should_run_test('e2e', 'e2e') is True
