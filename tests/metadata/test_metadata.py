import pytest
import time

def test_get_service_endpoint(metadata_provider_instance):
    assert metadata_provider_instance.get_service_endpoint() == f'{metadata_provider_instance.url}/' + '{did}'


def test_publish_valid_ddo(asset1, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    assert metadata_provider_instance.get_asset_ddo(asset1.did)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_publish_invalid_ddo(metadata_provider_instance):
    with pytest.raises(AttributeError):
        metadata_provider_instance.publish_asset_ddo({})


def test_publish_ddo_already_registered(asset1, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    with pytest.raises(ValueError):
        metadata_provider_instance.publish_asset_ddo(asset1)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_get_asset_ddo_for_not_registered_did(metadata_provider_instance):
    invalid_did = 'did:nv:not_valid'
    result = metadata_provider_instance.get_asset_ddo(invalid_did)
    assert result == {}


def test_get_asset_metadata(asset1, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    metadata_dict = metadata_provider_instance.get_asset_metadata(asset1.did)
    assert isinstance(metadata_dict, dict)
    assert 'main' in metadata_dict
    assert 'curation' in metadata_dict
    assert 'additionalInformation' in metadata_dict
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_get_asset_metadata_for_not_registered_did(metadata_provider_instance):
    invalid_did = 'did:nv:not_valid'
    metadata_dict = metadata_provider_instance.get_asset_metadata(invalid_did)
    assert metadata_dict == {}


def test_list_assets(asset1, metadata_provider_instance):
    ddo = metadata_provider_instance.publish_asset_ddo(asset1)

    # wait for it to be searcheable
    time.sleep(3)

    assert ddo['id'] == asset1.did
    assert ddo['id'] in metadata_provider_instance.list_assets()

    assets = metadata_provider_instance.list_assets()
    assert isinstance(assets, list)
    assert isinstance(assets[0], str)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_list_assets_ddo(asset1, metadata_provider_instance):
    ddo = metadata_provider_instance.publish_asset_ddo(asset1)

    # wait for it to be searcheable
    time.sleep(3)

    assert ddo['id'] == asset1.did
    assert ddo in metadata_provider_instance.list_assets_ddo()

    assert isinstance(metadata_provider_instance.list_assets_ddo(), list)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_update_ddo(asset1, asset2, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    metadata_provider_instance.update_asset_ddo(asset1.did, asset2)
    assert metadata_provider_instance.get_asset_ddo(asset1.did).did == asset2.did
    assert metadata_provider_instance.get_asset_ddo(asset1.did).metadata['main']['name'] != \
           asset1.metadata['main'][
               'name'], 'The name has not been updated correctly.'
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_update_with_not_valifd_ddo(asset1, metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.update_asset_ddo(asset1.did, {})


def test_text_search(asset1, asset2, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    # wait for it to be searcheable
    time.sleep(3)

    result = metadata_provider_instance.text_search(text='Weather information', offset=10000)
    number_matches = result['total_results']['value']
    assert number_matches > 0

    text = 'UK'
    metadata_provider_instance.publish_asset_ddo(asset2)
    # wait for it to be searcheable
    time.sleep(3)

    result = metadata_provider_instance.text_search(text=text, offset=10000)
    number_matches = result['total_results']['value']
    assert number_matches > 0

    metadata_provider_instance.retire_asset_ddo(asset1.did)
    metadata_provider_instance.retire_asset_ddo(asset2.did)


def test_text_search_invalid_query(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.text_search(text='', offset='Invalid')


def test_query_search(asset1, metadata_provider_instance):
    search_query = {
        "query": {
            "bool": {
                "must": [{
                    "match": {"service.attributes.main.type": "dataset"}
                }]
            }
        }
    }

    metadata_provider_instance.publish_asset_ddo(asset1)
    # wait for it to be searcheable
    time.sleep(3)

    result = metadata_provider_instance.query_search(search_query=search_query, offset=10000)
    number_matches = result['total_results']['value']
    assert number_matches > 0

    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_query_search_invalid_query(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.query_search(search_query='')


def test_retire_ddo(asset1, metadata_provider_instance):
    n = len(metadata_provider_instance.list_assets())
    metadata_provider_instance.publish_asset_ddo(asset1)

    # wait for elasticsearch
    time.sleep(3)

    response = metadata_provider_instance.retire_asset_ddo(asset1.did)
    assert response.ok is True

def test_retire_not_published_did(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.retire_asset_ddo('did:nv:not_registered')
