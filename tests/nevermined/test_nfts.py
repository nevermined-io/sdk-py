import time

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from common_utils_py.ddo.ddo import DDO

from examples import ExampleConfig
from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper
from tests.resources.helper_functions import (get_consumer_account, get_publisher_account,
                                              log_event, get_registered_ddo_nft)


def test_nfts_flow(publisher_instance_no_init, consumer_instance_no_init):
    config = ExampleConfig.get_config()
    keeper = Keeper.get_instance()

    pub_acc = get_publisher_account()

    # Register ddo
    ddo = get_registered_ddo_nft(publisher_instance_no_init, pub_acc)
    asset_id = ddo.asset_id
    nft_amounts = 1
    assert isinstance(ddo, DDO)

    consumer_account = get_consumer_account()

    consumer_instance_no_init.accounts.request_tokens(consumer_account, 100)

    service_sales = ddo.get_service(service_type=ServiceTypes.NFT_SALES)
    sa_sales = ServiceAgreement.from_service_dict(service_sales.as_dictionary())

    amounts = sa_sales.get_amounts_int()
    receivers = sa_sales.get_receivers()
    number_nfts = sa_sales.get_number_nfts()
    token_address = keeper.token.address

    sales_agreement_id = consumer_instance_no_init.assets.order(
        ddo.did, sa_sales.index, consumer_account, consumer_account)

    sales_agreement = keeper.agreement_manager.get_agreement(sales_agreement_id)
    assert sales_agreement.did == asset_id, ''

    lock_cond_id = sales_agreement.condition_ids[0]
    access_cond_id = sales_agreement.condition_ids[1]
    escrow_cond_id = sales_agreement.condition_ids[2]

    # transfer the nft
    keeper.transfer_nft_condition.fulfill(
        sales_agreement_id,
        asset_id,
        consumer_account.address,
        nft_amounts,
        lock_cond_id,
        pub_acc
    )

    # escrow payment
    keeper.escrow_payment_condition.fulfill(
        sales_agreement_id,
        asset_id,
        amounts,
        receivers,
        keeper.escrow_payment_condition.address,
        token_address,
        lock_cond_id,
        access_cond_id,
        pub_acc
    )

    assert keeper.condition_manager.get_condition_state(lock_cond_id) == 2, ''
    assert keeper.condition_manager.get_condition_state(access_cond_id) == 2, ''
    assert keeper.condition_manager.get_condition_state(escrow_cond_id) == 2, ''

    assert keeper.did_registry.balance(consumer_account.address, asset_id) >= number_nfts


    # CHECK ACCESS CREATING THE AGREEMENT
    nft_access_service_agreement = ServiceAgreement.from_ddo(ServiceTypes.NFT_ACCESS, ddo)
    sa_access = ddo.get_service(service_type=ServiceTypes.NFT_ACCESS)
    nft_access_agreement_id = consumer_instance_no_init.assets.order(
        ddo.did, sa_access.index, consumer_account, consumer_account)

    event = keeper.nft_access_template.subscribe_agreement_created(
        nft_access_agreement_id,
        10,
        log_event(keeper.nft_access_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AgreementCreated '

    time.sleep(3)
    keeper.nft_holder_condition.fulfill(
        nft_access_agreement_id, asset_id, consumer_account.address, number_nfts, consumer_account
    )
    time.sleep(3)
    keeper.nft_access_condition.fulfill(
        nft_access_agreement_id, asset_id, consumer_account.address, pub_acc
    )
    time.sleep(3)

    access_agreement = keeper.agreement_manager.get_agreement(nft_access_agreement_id)
    assert access_agreement.did == asset_id, ''

    nft_holder_cond_id = access_agreement.condition_ids[0]
    nft_access_cond_id = access_agreement.condition_ids[1]

    assert keeper.condition_manager.get_condition_state(nft_access_cond_id) == 2, ''
    assert keeper.condition_manager.get_condition_state(nft_holder_cond_id) == 2, ''

    # AND HERE TESTING WITHOUT CREATING THE AGREEMENT
    service_access = ddo.get_service(service_type=ServiceTypes.NFT_ACCESS)

    no_agreement_id = '0x'

    assert consumer_instance_no_init.assets.access(
        no_agreement_id,
        ddo.did,
        service_access.index,
        consumer_account,
        config.downloads_path,
        service_type=ServiceTypes.NFT_ACCESS
    )

    # AND HERE CHECKING CREATING AN AGREEMENT FIRST
    nft_access_service_agreement = ServiceAgreement.from_ddo(ServiceTypes.NFT_ACCESS, ddo)
    nft_access_agreement_id = ServiceAgreement.create_new_agreement_id()
    (nft_access_cond_id, nft_holder_cond_id) = nft_access_service_agreement.generate_agreement_condition_ids(
        nft_access_agreement_id, asset_id, consumer_account.address, keeper)

    keeper.nft_access_template.create_agreement(
        nft_access_agreement_id,
        asset_id,
        [nft_holder_cond_id, nft_access_cond_id],
        nft_access_service_agreement.conditions_timelocks,
        nft_access_service_agreement.conditions_timeouts,
        consumer_account.address,
        pub_acc
    )

    event = keeper.nft_access_template.subscribe_agreement_created(
        nft_access_agreement_id,
        10,
        log_event(keeper.nft_access_template.AGREEMENT_CREATED_EVENT),
        (),
        wait=True
    )
    assert event, 'no event for AgreementCreated '

    # This is because in this test the gateway is executed using the same account than the consumer
    keeper.did_registry.add_provider(asset_id, consumer_account.address, pub_acc)
    time.sleep(3)

    assert consumer_instance_no_init.assets.access(
        nft_access_agreement_id,
        ddo.did,
        service_access.index,
        consumer_account,
        config.downloads_path,
        index=0,
        service_type=ServiceTypes.NFT_ACCESS
    )
