import time
import pytest

from examples import ExampleConfig
from tests.resources.helper_functions import get_algorithm_ddo, get_metadata
from nevermined_sdk_py import ConfigProvider


def create_compute_retry(nevermined, metadata, account):
    retry = 0
    ddo = None
    while True:
        try:
            ddo = nevermined.assets.create_compute(metadata, account)
        except ValueError:
            pass
        if ddo is not None or retry == 3:
            return ddo
        retry += 1
        time.sleep(5)


def create_retry(nevermined, metadata, account, providers=None):
    retry = 0
    ddo = None
    while True:
        try:
            ddo = nevermined.assets.create(metadata, account, providers=providers)
        except ValueError:
            pass
        if ddo is not None or retry == 3:
            return ddo
        retry += 1
        time.sleep(5)


def test_publisher_download_compute(publisher_instance_no_init):
    config = ExampleConfig.get_config()
    publisher = publisher_instance_no_init.main_account
    metadata = get_metadata()
    ddo = create_compute_retry(publisher_instance_no_init, metadata, publisher)
    assert ddo

    service_agreement = ddo.get_service("compute")
    assert publisher_instance_no_init.assets.download(
        ddo.did, service_agreement.index, publisher, config.downloads_path
    )
    publisher_instance_no_init.assets.retire(ddo.did)


def test_consumer_download_compute(
    publisher_instance_no_init, consumer_instance_no_init
):
    config = ExampleConfig.get_config()
    publisher = publisher_instance_no_init.main_account
    consumer = consumer_instance_no_init.main_account
    metadata = get_metadata()

    # publisher creates compute asset
    ddo = create_compute_retry(publisher_instance_no_init, metadata, publisher)
    assert ddo

    # consumer orders compute asset
    service_agreement = ddo.get_service("compute")
    _agreement_id = consumer_instance_no_init.assets.order(
        ddo.did, service_agreement.index, consumer
    )

    # consumer tries to download the asset
    with pytest.raises(ValueError):
        consumer_instance_no_init.assets.download(
            ddo.did, service_agreement.index, consumer, config.downloads_path
        )
    publisher_instance_no_init.assets.retire(ddo.did)


def test_publisher_download_algorithm(publisher_instance_no_init):
    config = ExampleConfig.get_config()
    publisher = publisher_instance_no_init.main_account
    metadata = get_algorithm_ddo()["service"][0]
    ddo = create_retry(publisher_instance_no_init, metadata["attributes"], publisher)
    assert ddo

    service_agreement = ddo.get_service("access")
    assert publisher_instance_no_init.assets.download(
        ddo.did, service_agreement.index, publisher, config.downloads_path
    )
    publisher_instance_no_init.assets.retire(ddo.did)


def test_provider_download_algorithm(
    publisher_instance_no_init, consumer_instance_no_init
):
    config = ExampleConfig.get_config()
    provider = publisher_instance_no_init.main_account
    consumer = consumer_instance_no_init.main_account
    metadata = get_algorithm_ddo()["service"][0]

    # consumer creates algorithm asset (for a compute job)
    ddo = create_retry(consumer_instance_no_init, metadata["attributes"], consumer, providers=[provider.address])
    assert ddo

    # provider downloads the asset
    service_agreement = ddo.get_service("access")
    assert publisher_instance_no_init.assets.download(
        ddo.did, service_agreement.index, consumer, config.downloads_path
    )
    publisher_instance_no_init.assets.retire(ddo.did)
