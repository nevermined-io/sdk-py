import pytest

from examples import ExampleConfig
from tests.resources.helper_functions import (get_algorithm_ddo,
                                              get_consumer_instance,
                                              get_publisher_instance)


def test_publisher_download_compute(metadata):
    config = ExampleConfig.get_config()
    publisher_instance = get_publisher_instance(True, False, False)
    publisher = publisher_instance.main_account
    ddo = publisher_instance.assets.create_compute(metadata, publisher)
    assert ddo

    service_agreement = ddo.get_service("compute")
    assert publisher_instance.assets.download(
        ddo.did, service_agreement.index, publisher, config.downloads_path
    )
    publisher_instance.assets.retire(ddo.did)


def test_consumer_download_compute(metadata):
    config = ExampleConfig.get_config()
    publisher_instance = get_publisher_instance(True, False, False)
    publisher = publisher_instance.main_account
    consumer_instance = get_consumer_instance(True, False, False)
    consumer = consumer_instance.main_account

    # publisher creates compute asset
    ddo = publisher_instance.assets.create_compute(metadata, publisher)
    assert ddo

    # consumer orders compute asset
    service_agreement = ddo.get_service("compute")
    _agreement_id = consumer_instance.assets.order(
        ddo.did, service_agreement.index, consumer, consumer
    )

    # consumer tries to download the asset
    with pytest.raises(ValueError):
        consumer_instance.assets.download(
            ddo.did, service_agreement.index, consumer, config.downloads_path
        )
    publisher_instance.assets.retire(ddo.did)


def test_publisher_download_algorithm(ddo_algorithm):
    config = ExampleConfig.get_config()
    publisher_instance = get_publisher_instance(True, False, False)
    publisher = publisher_instance.main_account
    metadata = ddo_algorithm["service"][0]
    ddo = publisher_instance.assets.create(metadata["attributes"], publisher)
    assert ddo

    service_agreement = ddo.get_service("access")
    assert publisher_instance.assets.download(
        ddo.did, service_agreement.index, publisher, config.downloads_path
    )
    publisher_instance.assets.retire(ddo.did)


def test_provider_download_algorithm(ddo_algorithm):
    config = ExampleConfig.get_config()
    publisher_instance = get_publisher_instance(True, False, False)
    provider = publisher_instance.main_account
    consumer_instance = get_consumer_instance(True, False, False)
    consumer = consumer_instance.main_account
    metadata = ddo_algorithm["service"][0]

    # consumer creates algorithm asset (for a compute job)
    ddo = consumer_instance.assets.create(
        metadata["attributes"], consumer, providers=[provider.address]
    )
    assert ddo

    # provider downloads the asset
    service_agreement = ddo.get_service("access")
    assert publisher_instance.assets.download(
        ddo.did, service_agreement.index, consumer, config.downloads_path
    )
    consumer_instance.assets.retire(ddo.did)
