#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import pytest
from common_utils_py.metadata.metadata import Metadata
from common_utils_py.ddo.ddo import DDO
from common_utils_py.did import DID

from nevermind_sdk_py import ConfigProvider
from tests.resources.helper_functions import get_resource_path
from tests.resources.tiers import e2e_test, should_run_test

if should_run_test('e2e'):
    metadata_provider = Metadata(ConfigProvider.get_config().metadata_url)


def _get_asset(file_name):
    sample_ddo_path = get_resource_path('ddo', file_name)
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)
    return DDO(json_filename=sample_ddo_path)


@pytest.fixture
def asset1():
    asset = _get_asset('ddo_sample1.json')
    asset._did = DID.did(asset.proof['checksum'])
    yield asset
    metadata_provider.retire_all_assets()


@pytest.fixture
def asset2():
    asset = _get_asset('ddo_sample2.json')
    asset._did = DID.did(asset.proof['checksum'])
    return asset


@pytest.fixture
def asset3():
    asset = _get_asset('ddo_sample3.json')
    asset._did = DID.did(asset.proof['checksum'])
    return asset


@e2e_test
def test_get_service_endpoint():
    assert metadata_provider.get_service_endpoint() == f'{metadata_provider.url}/' + '{did}'


@e2e_test
def test_publish_valid_ddo(asset1):
    metadata_provider.publish_asset_ddo(asset1)
    assert metadata_provider.get_asset_ddo(asset1.did)
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_publish_invalid_ddo():
    with pytest.raises(AttributeError):
        metadata_provider.publish_asset_ddo({})


@e2e_test
def test_publish_ddo_already_registered(asset1):
    metadata_provider.publish_asset_ddo(asset1)
    with pytest.raises(ValueError):
        metadata_provider.publish_asset_ddo(asset1)
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_get_asset_ddo_for_not_registered_did():
    invalid_did = 'did:op:not_valid'
    with pytest.raises(ValueError):
        metadata_provider.get_asset_ddo(invalid_did)


@e2e_test
def test_get_asset_metadata(asset1):
    metadata_provider.publish_asset_ddo(asset1)
    metadata_dict = metadata_provider.get_asset_metadata(asset1.did)
    assert isinstance(metadata_dict, dict)
    assert 'main' in metadata_dict
    assert 'curation' in metadata_dict
    assert 'additionalInformation' in metadata_dict
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_get_asset_metadata_for_not_registered_did():
    invalid_did = 'did:op:not_valid'
    with pytest.raises(ValueError):
        metadata_provider.get_asset_metadata(invalid_did)


@e2e_test
def test_list_assets(asset1):
    num_assets = len(metadata_provider.list_assets())
    metadata_provider.publish_asset_ddo(asset1)
    assert len(metadata_provider.list_assets()) == (num_assets + 1)
    assert isinstance(metadata_provider.list_assets(), list)
    assert isinstance(metadata_provider.list_assets()[0], str)
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_list_assets_ddo(asset1):
    num_assets = len(metadata_provider.list_assets_ddo())
    metadata_provider.publish_asset_ddo(asset1)
    assert len(metadata_provider.list_assets_ddo()) == (num_assets + 1)
    assert isinstance(metadata_provider.list_assets_ddo(), dict)
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_update_ddo(asset1, asset2):
    metadata_provider.publish_asset_ddo(asset1)
    metadata_provider.update_asset_ddo(asset1.did, asset2)
    assert metadata_provider.get_asset_ddo(asset1.did).did == asset2.did
    assert metadata_provider.get_asset_ddo(asset1.did).metadata['main']['name'] != asset1.metadata['main'][
        'name'], 'The name has not been updated correctly.'
    metadata_provider.retire_asset_ddo(asset1.did)


@e2e_test
def test_update_with_not_valid_ddo(asset1):
    with pytest.raises(Exception):
        metadata_provider.update_asset_ddo(asset1.did, {})


@e2e_test
def test_text_search(asset1, asset3):
    office_matches = 0
    metadata_provider.publish_asset_ddo(asset1)
    assert len(metadata_provider.text_search(text='Weather information', offset=10000)['results']) == (
            office_matches + 1)

    text = '0c184915b07b44c888d468be85a9b28253e80070e5294b1aaed81c2f0264e430'
    id_matches2 = len(metadata_provider.text_search(text=text, offset=10000)['results'])
    metadata_provider.publish_asset_ddo(asset3)
    assert len(metadata_provider.text_search(text=text, offset=10000)['results']) == (id_matches2 + 1)

    assert len(metadata_provider.text_search(text='Weather information', offset=10000)['results']) == (
            office_matches + 2)
    metadata_provider.retire_asset_ddo(asset1.did)
    metadata_provider.retire_asset_ddo(asset3.did)


@e2e_test
def test_text_search_invalid_query():
    with pytest.raises(Exception):
        metadata_provider.text_search(text='', offset='Invalid')


# @e2e_test
# def test_query_search(asset1, asset3):
#     num_matches = 0
#     metadata_provider.publish_asset_ddo(asset1)
#
#     assert len(metadata_provider.query_search(search_query={"query": {"type": ["dataset"]}},
#                                      offset=10000)['results']) == (
#                    num_matches + 1)
#
#     metadata_provider.publish_asset_ddo(asset3)
#
#     assert len(metadata_provider.query_search(search_query={"query": {"type": ["dataset"]}},
#                                      offset=10000)['results']) == (
#                    num_matches + 2)
#     metadata_provider.retire_asset_ddo(asset1.did)
#     metadata_provider.retire_asset_ddo(asset3.did)


@e2e_test
def test_query_search_invalid_query():
    with pytest.raises(Exception):
        metadata_provider.query_search(search_query='')


@e2e_test
def test_retire_ddo(asset1):
    n = len(metadata_provider.list_assets())
    metadata_provider.publish_asset_ddo(asset1)
    assert len(metadata_provider.list_assets()) == (n + 1)
    metadata_provider.retire_asset_ddo(asset1.did)
    assert len(metadata_provider.list_assets()) == n


@e2e_test
def test_retire_all_ddos(asset1):
    metadata_provider.retire_all_assets()
    assert len(metadata_provider.list_assets()) == 0


@e2e_test
def test_retire_not_published_did():
    with pytest.raises(Exception):
        metadata_provider.retire_asset_ddo('did:op:not_registered')


@e2e_test
def test_validate_metadata(metadata):
    assert metadata_provider.validate_metadata(metadata)


@e2e_test
def test_validate_invalid_metadata():
    assert not metadata_provider.validate_metadata({})
