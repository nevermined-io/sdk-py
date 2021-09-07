import pytest

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
    with pytest.raises(ValueError):
        metadata_provider_instance.get_asset_ddo(invalid_did)


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
    with pytest.raises(ValueError):
        metadata_provider_instance.get_asset_metadata(invalid_did)


def test_list_assets(asset1, metadata_provider_instance):
    num_assets = len(metadata_provider_instance.list_assets())
    metadata_provider_instance.publish_asset_ddo(asset1)
    assert len(metadata_provider_instance.list_assets()) == (num_assets + 1)
    assets = metadata_provider_instance.list_assets()
    assert isinstance(assets, list)
    assert isinstance(assets[0], str)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_list_assets_ddo(asset1, metadata_provider_instance):
    num_assets = len(metadata_provider_instance.list_assets_ddo())
    metadata_provider_instance.publish_asset_ddo(asset1)
    assert len(metadata_provider_instance.list_assets_ddo()) == (num_assets + 1)
    assert isinstance(metadata_provider_instance.list_assets_ddo(), dict)
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_update_ddo(asset1, asset2, metadata_provider_instance):
    metadata_provider_instance.publish_asset_ddo(asset1)
    metadata_provider_instance.update_asset_ddo(asset1.did, asset2)
    assert metadata_provider_instance.get_asset_ddo(asset1.did).did == asset2.did
    assert metadata_provider_instance.get_asset_ddo(asset1.did).metadata['main']['name'] != \
           asset1.metadata['main'][
               'name'], 'The name has not been updated correctly.'
    metadata_provider_instance.retire_asset_ddo(asset1.did)


def test_update_with_not_valid_ddo(asset1, metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.update_asset_ddo(asset1.did, {})


def test_text_search(asset1, asset2, metadata_provider_instance):
    office_matches = 0
    metadata_provider_instance.publish_asset_ddo(asset1)
    assert len(
        metadata_provider_instance.text_search(text='Weather information', offset=10000)['results']) == (
                   office_matches + 1)

    text = 'UK'
    id_matches2 = len(metadata_provider_instance.text_search(text=text, offset=10000)['results'])
    metadata_provider_instance.publish_asset_ddo(asset2)
    assert len(metadata_provider_instance.text_search(text=text, offset=10000)['results']) == (
            id_matches2 + 1)

    assert len(
        metadata_provider_instance.text_search(text='Weather information', offset=10000)['results']) == (
                   office_matches + 2)
    metadata_provider_instance.retire_asset_ddo(asset1.did)
    metadata_provider_instance.retire_asset_ddo(asset2.did)


def test_text_search_invalid_query(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.text_search(text='', offset='Invalid')


def test_query_search(asset1, asset2, metadata_provider_instance):
    num_matches = 0
    metadata_provider_instance.publish_asset_ddo(asset1)

    assert len(metadata_provider_instance.query_search(search_query={"query": {"type": ["dataset"]}},
                                              offset=10000)['results']) == (
                   num_matches + 1)

    metadata_provider_instance.publish_asset_ddo(asset2)

    assert len(metadata_provider_instance.query_search(search_query={"query": {"type": ["dataset"]}},
                                              offset=10000)['results']) == (
                   num_matches + 2)
    metadata_provider_instance.retire_asset_ddo(asset1.did)
    metadata_provider_instance.retire_asset_ddo(asset2.did)


def test_query_search_invalid_query(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.query_search(search_query='')


def test_retire_ddo(asset1, metadata_provider_instance):
    n = len(metadata_provider_instance.list_assets())
    metadata_provider_instance.publish_asset_ddo(asset1)
    assert len(metadata_provider_instance.list_assets()) == (n + 1)
    metadata_provider_instance.retire_asset_ddo(asset1.did)
    assert len(metadata_provider_instance.list_assets()) == n


def test_retire_all_ddos(asset1, metadata_provider_instance):
    metadata_provider_instance.retire_all_assets()
    assert len(metadata_provider_instance.list_assets()) == 0


def test_retire_not_published_did(metadata_provider_instance):
    with pytest.raises(Exception):
        metadata_provider_instance.retire_asset_ddo('did:nv:not_registered')
