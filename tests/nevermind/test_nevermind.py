def test_ocean_instance(publisher_instance):
    assert publisher_instance.tokens
    assert publisher_instance.agreements
    assert publisher_instance.assets
    assert publisher_instance.accounts
    assert publisher_instance.services
    assert publisher_instance.auth
    assert publisher_instance.templates
    assert publisher_instance.secret_store
