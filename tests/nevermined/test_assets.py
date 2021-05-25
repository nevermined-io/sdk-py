import logging
from contracts_lib_py.keeper import Keeper

import pytest
from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_factory import ServiceDescriptor
from common_utils_py.agreements.service_types import ServiceTypes, ServiceTypesIndices
from common_utils_py.did import DID, did_to_id
from contracts_lib_py.exceptions import DIDNotFound
from contracts_lib_py.web3_provider import Web3Provider
from eth_utils import add_0x_prefix

from tests.resources.helper_functions import log_event


def create_asset(publisher_instance, ddo_sample):
    nevermined = publisher_instance
    acct = nevermined.main_account
    asset = ddo_sample
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(
        {'main': {'service': 'SecretStore', 'publicKey': '0casd',
                  'threshold': '1'}}, my_secret_store)
    return nevermined.assets.create(asset.metadata, acct, [auth_service])


def test_register_asset(publisher_instance, ddo_sample):
    logging.debug("".format())
    ##########################################################
    # Setup account
    ##########################################################
    publisher = publisher_instance.main_account

    # ensure Nevermined token balance
    if publisher_instance.accounts.balance(publisher).ocn == 0:
        publisher_instance.accounts.request_tokens(publisher, 200)

    # You will need some token to make this transfer!
    assert publisher_instance.accounts.balance(publisher).ocn > 0

    ##########################################################
    # Create an asset DDO with valid metadata
    ##########################################################
    asset = ddo_sample

    ##########################################################
    # Register using high-level interface
    ##########################################################
    ddo = publisher_instance.assets.create(asset.metadata, publisher)
    publisher_instance.assets.retire(ddo.did)


def test_resolve_did(publisher_instance, metadata):
    # prep ddo
    # metadata = Metadata.get_example()
    publisher = publisher_instance.main_account
    # happy path
    original_ddo = publisher_instance.assets.create(metadata, publisher, activity_id=publisher.address, attributes='test123')
    did = original_ddo.did
    ddo = publisher_instance.assets.resolve(did).as_dictionary()
    original = original_ddo.as_dictionary()
    assert ddo['publicKey'] == original['publicKey']
    assert ddo['authentication'] == original['authentication']
    assert ddo['service']
    assert original['service']
    metadata = ddo['service'][0]['attributes']
    if 'datePublished' in metadata['main']:
        metadata['main'].pop('datePublished')
    assert ddo['service'][0]['attributes']['main']['name'] == \
           original['service'][0]['attributes']['main']['name']
    assert ddo['service'][1] == original['service'][1]

    # Can't resolve unregistered asset
    unregistered_did = DID.encoded_did({"0": "0x00112233445566"})
    with pytest.raises(DIDNotFound):
        publisher_instance.assets.resolve(unregistered_did)

    # Raise error on bad did
    invalid_did = "did:nv:0123456789"
    with pytest.raises(DIDNotFound):
        publisher_instance.assets.resolve(invalid_did)
    publisher_instance.assets.retire(did)


def test_create_data_asset(publisher_instance, consumer_instance, ddo_sample):
    """
    Setup accounts and asset, register this asset on Nevermined Metadata.
    """

    logging.debug("".format())
    ##########################################################
    # Setup 2 accounts
    ##########################################################
    publisher_acct = publisher_instance.main_account
    consumer_acct = consumer_instance.main_account

    # ensure Nevermined token balance
    if publisher_instance.accounts.balance(publisher_acct).ocn == 0:
        rcpt = publisher_instance.accounts.request_tokens(publisher_acct, 200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)
    if consumer_instance.accounts.balance(consumer_acct).ocn == 0:
        rcpt = consumer_instance.accounts.request_tokens(consumer_acct, 200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # You will need some token to make this transfer!
    assert publisher_instance.accounts.balance(publisher_acct).ocn > 0
    assert consumer_instance.accounts.balance(consumer_acct).ocn > 0

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################
    asset = ddo_sample

    ##########################################################
    # List currently published assets
    ##########################################################
    meta_data_assets = publisher_instance.assets.search('')
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    if asset.did in meta_data_assets:
        publisher_instance.assets.resolve(asset.did)
        publisher_instance.assets.retire(asset.did)
    # Publish the metadata
    new_asset = publisher_instance.assets.create(asset.metadata, publisher_acct)

    # get_asset_metadata only returns 'main' key, is this correct?
    published_metadata = consumer_instance.assets.resolve(new_asset.did)

    assert published_metadata
    # only compare top level keys
    assert sorted(list(asset.metadata['main'].keys())).remove('files') == sorted(
        list(published_metadata.metadata.keys())).remove('encryptedFiles')
    publisher_instance.assets.retire(new_asset.did)


def test_create_asset_with_different_secret_store(publisher_instance, ddo_sample):
    acct = publisher_instance.main_account

    asset = ddo_sample
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(
        {'main': {'service': 'SecretStore', 'publicKey': '0casd',
                  'threshold': '1'}}, my_secret_store)
    new_asset = publisher_instance.assets.create(asset.metadata, acct, [auth_service])
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION).service_endpoint == my_secret_store
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)
    publisher_instance.assets.retire(new_asset.did)

    access_service = ServiceDescriptor.access_service_descriptor(
        {"main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": '0x1234',
            "price": '1',
            "timeout": 3600,
            "datePublished": '2019-08-30T12:19:54Z'
        }}, ''
    )
    new_asset = publisher_instance.assets.create(asset.metadata, acct, [access_service])
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION)
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)
    publisher_instance.assets.retire(new_asset.did)

    new_asset = publisher_instance.assets.create(asset.metadata, acct)
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION)
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)
    publisher_instance.assets.retire(new_asset.did)


def test_asset_owner(publisher_instance, ddo_sample):
    acct = publisher_instance.main_account

    asset = ddo_sample
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(
        {'main': {'service': 'SecretStore', 'publicKey': '0casd',
                  'threshold': '1'}}, my_secret_store)
    new_asset = publisher_instance.assets.create(asset.metadata, acct, [auth_service])

    assert publisher_instance.assets.owner(new_asset.did) == acct.address
    publisher_instance.assets.retire(new_asset.did)


def test_owner_assets(publisher_instance, ddo_sample):
    acct = publisher_instance.main_account
    assets_owned = len(publisher_instance.assets.owner_assets(acct.address))
    asset = create_asset(publisher_instance, ddo_sample)
    assert len(publisher_instance.assets.owner_assets(acct.address)) == assets_owned + 1
    publisher_instance.assets.retire(asset.did)


def test_assets_consumed(publisher_instance, consumer_instance, ddo_sample):
    acct = consumer_instance.main_account
    consumed_assets = len(publisher_instance.assets.consumer_assets(acct.address))
    asset = create_asset(publisher_instance, ddo_sample)
    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    service_dict = service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service_dict)
    keeper = publisher_instance.keeper

    def grant_access(event, instance, agr_id, did, cons_address, account):
        instance.agreements.conditions.grant_access(
            agr_id, add_0x_prefix(did_to_id(did)), cons_address, account)

    agreement_id = consumer_instance.assets.order(
        asset.did, sa.index, acct, acct)
    keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        15,
        grant_access,
        (publisher_instance, agreement_id, asset.did,
         acct.address, publisher_instance.main_account),
        wait=True
    )

    keeper.access_condition.subscribe_condition_fulfilled(
        agreement_id,
        15,
        log_event(keeper.access_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert publisher_instance.agreements.is_access_granted(agreement_id, asset.did, acct.address)

    assert len(publisher_instance.assets.consumer_assets(acct.address)) == consumed_assets + 1
    publisher_instance.assets.retire(asset.did)


def test_assets_resolve(publisher_instance, metadata):
    publisher = publisher_instance.main_account
    ddo = publisher_instance.assets.create(metadata, publisher)
    ddo_resolved = publisher_instance.assets.resolve(ddo.did)
    assert ddo.did == ddo_resolved.did
    publisher_instance.assets.retire(ddo.did)


def test_assets_search(publisher_instance, metadata):
    publisher = publisher_instance.main_account
    ddo = publisher_instance.assets.create(metadata, publisher)
    assert len(publisher_instance.assets.search('Monkey')) > 0
    publisher_instance.assets.retire(ddo.did)


def test_assets_algorithm(publisher_instance, algorithm_ddo):
    # Allow publish an algorithm
    publisher = publisher_instance.main_account
    metadata = algorithm_ddo['service'][0]
    ddo = publisher_instance.assets.create(metadata['attributes'], publisher)
    assert ddo
    publisher_instance.assets.retire(ddo.did)


def test_assets_workflow(publisher_instance, workflow_ddo):
    # Allow publish an workflow
    publisher = publisher_instance.main_account
    metadata = workflow_ddo['service'][0]
    ddo = publisher_instance.assets.create(metadata['attributes'], publisher)
    assert ddo
    publisher_instance.assets.retire(ddo.did)


def test_assets_compute(publisher_instance, metadata):
    publisher = publisher_instance.main_account
    asset_rewards = {
        "_amounts": ["10", "2"],
        "_receivers": ["0x00Bd138aBD70e2F00903268F3Db08f2D25677C9e", "0x068ed00cf0441e4829d9784fcbe7b9e26d4bd8d0"]
    }
    ddo = publisher_instance.assets.create_compute(metadata, publisher, asset_rewards=asset_rewards)
    assert ddo
    publisher_instance.assets.retire(ddo.did)


def test_transfer_ownership(publisher_instance, metadata, consumer_instance):
    publisher = publisher_instance.main_account
    consumer = consumer_instance.main_account
    ddo = publisher_instance.assets.create(metadata, publisher)
    owner = publisher_instance.assets.owner(ddo.did)
    assert owner == publisher.address
    publisher_instance.assets.transfer_ownership(ddo.did, consumer.address, publisher)
    assert publisher_instance.assets.owner(ddo.did) == consumer.address
    publisher_instance.assets.retire(ddo.did)


def test_grant_permissions(publisher_instance, metadata, consumer_instance):
    publisher = publisher_instance.main_account
    consumer = consumer_instance.main_account
    ddo = publisher_instance.assets.create(metadata, publisher)

    assert not publisher_instance.assets.get_permissions(ddo.did, consumer.address)
    publisher_instance.assets.delegate_persmission(ddo.did, consumer.address, publisher)
    assert publisher_instance.assets.get_permissions(ddo.did, consumer.address)
    publisher_instance.assets.revoke_permissions(ddo.did, consumer.address, publisher)
    assert not publisher_instance.assets.get_permissions(ddo.did, consumer.address)

    publisher_instance.assets.retire(ddo.did)


def test_execute_workflow(publisher_instance_no_init, consumer_instance_no_init, metadata, algorithm_ddo, workflow_ddo):
    consumer = publisher_instance_no_init.main_account
    publisher = consumer_instance_no_init.main_account

    # publish compute
    ddo_computing = publisher_instance_no_init.assets.create_compute(metadata, publisher)

    # publish algorithm
    metadata = algorithm_ddo['service'][0]
    ddo_algorithm = consumer_instance_no_init.assets.create(metadata['attributes'], consumer)

    metadata = workflow_ddo['service'][0]
    metadata['attributes']['main']['workflow']['stages'][0]['input'][0]['id'] = ddo_computing.did
    metadata['attributes']['main']['workflow']['stages'][0]['transformation']['id'] = ddo_algorithm.did
    workflow_ddo = consumer_instance_no_init.assets.create(metadata['attributes'], publisher)
    assert workflow_ddo

    # order compute asset
    service = ddo_computing.get_service(service_type=ServiceTypes.CLOUD_COMPUTE)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = consumer_instance_no_init.assets.order(ddo_computing.did, sa.index, consumer, consumer)

    keeper = Keeper.get_instance()
    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Reward condition is not found"

    # execute workflow
    execution_id = consumer_instance_no_init.assets.execute(agreement_id, ddo_computing.did, sa.index, consumer,
        workflow_ddo.did)
    assert execution_id

    publisher_instance_no_init.assets.retire(ddo_computing.did)
    publisher_instance_no_init.assets.retire(ddo_algorithm.did)
    publisher_instance_no_init.assets.retire(workflow_ddo.did)


def test_compute_status(publisher_instance_no_init, consumer_instance_no_init, metadata, algorithm_ddo, workflow_ddo):
    consumer = publisher_instance_no_init.main_account
    publisher = consumer_instance_no_init.main_account

    # publish compute
    ddo_computing = publisher_instance_no_init.assets.create_compute(metadata, publisher)

    # publish algorithm
    metadata = algorithm_ddo['service'][0]
    ddo_algorithm = consumer_instance_no_init.assets.create(metadata['attributes'], consumer)

    metadata = workflow_ddo['service'][0]
    metadata['attributes']['main']['workflow']['stages'][0]['input'][0]['id'] = ddo_computing.did
    metadata['attributes']['main']['workflow']['stages'][0]['transformation']['id'] = ddo_algorithm.did
    workflow_ddo = consumer_instance_no_init.assets.create(metadata['attributes'], publisher)
    assert workflow_ddo

    # order compute asset
    service = ddo_computing.get_service(service_type=ServiceTypes.CLOUD_COMPUTE)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = consumer_instance_no_init.assets.order(ddo_computing.did, sa.index, consumer, consumer)

    keeper = Keeper.get_instance()
    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Reward condition is not found"

    # execute workflow
    execution_id = consumer_instance_no_init.assets.execute(agreement_id, ddo_computing.did, sa.index, consumer,
        workflow_ddo.did)

    # get status
    status = consumer_instance_no_init.assets.compute_status(agreement_id, execution_id, consumer)
    assert status

    publisher_instance_no_init.assets.retire(ddo_computing.did)
    publisher_instance_no_init.assets.retire(ddo_algorithm.did)
    publisher_instance_no_init.assets.retire(workflow_ddo.did)


def test_compute_logs(publisher_instance_no_init, consumer_instance_no_init, metadata, algorithm_ddo, workflow_ddo):
    consumer = publisher_instance_no_init.main_account
    publisher = consumer_instance_no_init.main_account

    # publish compute
    ddo_computing = publisher_instance_no_init.assets.create_compute(metadata, publisher)

    # publish algorithm
    metadata = algorithm_ddo['service'][0]
    ddo_algorithm = consumer_instance_no_init.assets.create(metadata['attributes'], consumer)

    metadata = workflow_ddo['service'][0]
    metadata['attributes']['main']['workflow']['stages'][0]['input'][0]['id'] = ddo_computing.did
    metadata['attributes']['main']['workflow']['stages'][0]['transformation']['id'] = ddo_algorithm.did
    workflow_ddo = consumer_instance_no_init.assets.create(metadata['attributes'], publisher)
    assert workflow_ddo

    # order compute asset
    service = ddo_computing.get_service(service_type=ServiceTypes.CLOUD_COMPUTE)
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = consumer_instance_no_init.assets.order(ddo_computing.did, sa.index, consumer, consumer)

    keeper = Keeper.get_instance()
    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Reward condition is not found"

    # execute workflow
    execution_id = consumer_instance_no_init.assets.execute(agreement_id, ddo_computing.did, sa.index, consumer,
        workflow_ddo.did)

    # get logs
    logs = consumer_instance_no_init.assets.compute_logs(agreement_id, execution_id, consumer)
    assert logs

    publisher_instance_no_init.assets.retire(ddo_computing.did)
    publisher_instance_no_init.assets.retire(ddo_algorithm.did)
    publisher_instance_no_init.assets.retire(workflow_ddo.did)


def test_agreement_direct(publisher_instance, consumer_instance, metadata):
    publisher_account = publisher_instance.main_account
    consumer_account = consumer_instance.main_account
    ddo = publisher_instance.assets.create(metadata, publisher_account,
                                                   providers=[
                                                       '0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0'])

    agreement_id = consumer_instance.assets.order(ddo.did,
                                                                 ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
                                                                 consumer_account,
                                                                 consumer_account
                                                                 )
    assert publisher_instance.agreements.status(agreement_id)

    keeper = publisher_instance.keeper

    event = keeper.lock_payment_condition.subscribe_condition_fulfilled(
        agreement_id,
        10,
        log_event(keeper.lock_payment_condition.FULFILLED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for LockRewardCondition.Fulfilled'

    assert publisher_instance.agreements.is_access_granted(agreement_id, ddo.did,
                                                                   consumer_account.address)
    publisher_instance.assets.retire(ddo.did)


def test_nfts(publisher_instance, metadata):
    publisher = publisher_instance.main_account
    someone_address = "0x00a329c0648769A73afAc7F9381E08FB43dBEA72"
    ddo = publisher_instance.assets.create(metadata, publisher, cap=100, royalties=0)

    balance = publisher_instance.nfts.balance(publisher.address, ddo.did)
    assert balance == 0
    balance_consumer = publisher_instance.nfts.balance(someone_address, ddo.did)
    assert balance_consumer == 0

    publisher_instance.nfts.mint(ddo.did, 10, account=publisher)
    assert balance + 10 == publisher_instance.nfts.balance(publisher.address, ddo.did)
    assert publisher_instance.nfts.transfer_nft(ddo.did, someone_address, 1, publisher)
    assert publisher_instance.nfts.balance(publisher.address, ddo.did) == 9
    assert publisher_instance.nfts.balance(someone_address, ddo.did) == balance_consumer + 1
    publisher_instance.nfts.burn(ddo.did, 9, account=publisher)
    assert balance == publisher_instance.nfts.balance(publisher.address, ddo.did)
    publisher_instance.assets.retire(ddo.did)