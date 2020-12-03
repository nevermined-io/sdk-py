import uuid


def new_did():
    return uuid.uuid4().hex + uuid.uuid4().hex


def test_get_provenance(publisher_instance, ddo_sample):
    publisher = publisher_instance.main_account
    activity_id = new_did()
    provenance_id = new_did()

    if publisher_instance.accounts.balance(publisher).ocn == 0:
        publisher_instance.accounts.request_tokens(publisher, 200)

    assert publisher_instance.accounts.balance(publisher).ocn > 0

    ddo = publisher_instance.assets.create(ddo_sample.metadata, publisher)

    assert publisher_instance.provenance.get_provenance_owner(ddo.did) == publisher.address

    publisher_instance.provenance.used(provenance_id, ddo.did, publisher.address, activity_id, "",
                                       account=publisher, attributes="used test")

    assert len(publisher_instance.provenance.get_did_provenance_events(ddo.did)) == 2

    provenance_entry = publisher_instance.provenance.get_provenance_entry(provenance_id)

    assert provenance_entry['activity_id'] == '0x' + activity_id
    assert provenance_entry['did'] == ddo.did
    assert provenance_entry['method'] == 3
    assert provenance_entry['created_by'] == publisher.address

    publisher_instance.assets.retire(ddo.did)


def test_delegate_provenance(publisher_instance, consumer_instance, ddo_sample):
    publisher = publisher_instance.main_account
    delegated = consumer_instance.main_account

    if publisher_instance.accounts.balance(publisher).ocn == 0:
        publisher_instance.accounts.request_tokens(publisher, 200)

    assert publisher_instance.accounts.balance(publisher).ocn > 0

    ddo = publisher_instance.assets.create(ddo_sample.metadata, publisher)

    assert publisher_instance.provenance.is_provenance_delegate(ddo.did, delegated.address) is False
    assert publisher_instance.provenance.add_did_provenance_delegate(ddo.did, delegated.address,
                                                                     publisher) is True
    assert publisher_instance.provenance.is_provenance_delegate(ddo.did, delegated.address) is True
    assert publisher_instance.provenance.remove_did_provenance_delegate(ddo.did, delegated.address,
                                                                        publisher) is True
    assert publisher_instance.provenance.is_provenance_delegate(ddo.did, delegated.address) is False


def test_search_multiple_provenance_event_tests(publisher_instance, ddo_sample):
    publisher = publisher_instance.main_account
    activity_id = new_did()
    provenance_id = new_did()
    derived_did = new_did()

    if publisher_instance.accounts.balance(publisher).ocn == 0:
        publisher_instance.accounts.request_tokens(publisher, 200)

    assert publisher_instance.accounts.balance(publisher).ocn > 0

    ddo = publisher_instance.assets.create(ddo_sample.metadata, publisher)

    publisher_instance.provenance.used(provenance_id, ddo.did, publisher.address, activity_id, "",
                                       account=publisher, attributes="used test")

    publisher_instance.provenance.was_derived_from(new_did(), derived_did, ddo.did,
                                                   publisher.address,
                                                   activity_id,
                                                   account=publisher, attributes="was derived from")

    publisher_instance.provenance.was_associated_with(new_did(), ddo.did, publisher.address,
                                                      activity_id,
                                                      account=publisher,
                                                      attributes="was associated with")

    publisher_instance.provenance.acted_on_behalf(new_did(), ddo.did, publisher.address,
                                                  publisher.address, activity_id, '',
                                                  account=publisher, attributes="acted on behalf")

    assert len(publisher_instance.provenance.get_did_provenance_methods_events('WAS_GENERATED_BY',
                                                                               ddo.did)) == 1
    assert len(
        publisher_instance.provenance.get_did_provenance_methods_events('USED', ddo.did)) == 1
    assert len(publisher_instance.provenance.get_did_provenance_methods_events('WAS_DERIVED_FROM',
                                                                               derived_did)) == 1
    assert len(
        publisher_instance.provenance.get_did_provenance_methods_events('WAS_ASSOCIATED_WITH',
                                                                        ddo.did)) == 1

    assert len(publisher_instance.provenance.get_did_provenance_methods_events('ACTED_ON_BEHALF',
                                                                               ddo.did)) == 1


def test_calling_twice_provenance(publisher_instance, ddo_sample):
    publisher = publisher_instance.main_account
    activity_id = new_did()
    provenance_id = new_did()

    if publisher_instance.accounts.balance(publisher).ocn == 0:
        publisher_instance.accounts.request_tokens(publisher, 200)

    assert publisher_instance.accounts.balance(publisher).ocn > 0

    ddo = publisher_instance.assets.create(ddo_sample.metadata, publisher)

    assert publisher_instance.provenance.used(provenance_id, ddo.did, publisher.address,
                                              activity_id, "",
                                              account=publisher, attributes="used test") is True

    assert publisher_instance.provenance.used(provenance_id, ddo.did, publisher.address,
                                              activity_id, "",
                                              account=publisher, attributes="used test") is False
