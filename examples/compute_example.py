import datetime
import logging
import os
import sys

from common_utils_py.agreements.service_agreement import ServiceAgreement
from common_utils_py.agreements.service_types import ServiceTypes
from contracts_lib_py.account import Account
from web3 import Web3

from examples import ExampleConfig, example_metadata
from nevermined_sdk_py import ConfigProvider, Nevermined
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper

PROVIDER_ADDRESS = os.getenv("PROVIDER_ADDRESS")
PROVIDER_PASSWORD = os.getenv("PROVIDER_PASSWORD")
PROVIDER_KEYFILE = os.getenv("PROVIDER_KEYFILE")


# Disable warnings emitted by web3
if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")


# this is so that we can change the `dateCreated` field in the ddos so that we
# avoid problems with duplicated ddos when running the demo
def dates_generator():
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=1)
    while True:
        now += delta
        yield now.isoformat(timespec="seconds") + "Z"


def configure_logging():
    level = os.getenv("LOGLEVEL", logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def compute_example(verbose=False):
    print("Setting up...")

    if verbose:
        configure_logging()

    date_created = dates_generator()

    # Setup nevermined
    ConfigProvider.set_config(ExampleConfig.get_config())
    config = ConfigProvider.get_config()
    nevermined = Nevermined()
    keeper = Keeper.get_instance()
    provider = "0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0"

    # Setup accounts
    acc = Account(
        Web3.toChecksumAddress(PROVIDER_ADDRESS), PROVIDER_PASSWORD, PROVIDER_KEYFILE
    )
    nevermined.accounts.request_tokens(acc, 10)
    provider_acc = acc
    consumer_acc = acc

    # Publish assets
    example_metadata.metadata["main"]["dateCreated"] = next(date_created)
    ddo_data = nevermined.assets.create(
        example_metadata.metadata, provider_acc, providers=[provider]
    )

    assert ddo_data is not None, "Creating data asset on-chain failed."
    print(f"[PROVIDER --> NEVERMINED] Publishing data asset: {ddo_data.did}")

    # Publish compute
    example_metadata.compute_ddo["main"]["dateCreated"] = next(date_created)
    ddo_compute = nevermined.assets.create(
        example_metadata.compute_ddo, provider_acc, providers=[provider]
    )
    assert ddo_compute is not None, "Creating compute asset on-chain failed."
    print(
        f"[PROVIDER --> NEVERMINED] Publishing compute to the data asset: {ddo_compute.did}"
    )

    # Publish algorithm
    example_metadata.algo_metadata["main"]["dateCreated"] = next(date_created)
    ddo_transformation = nevermined.assets.create(
        example_metadata.algo_metadata, consumer_acc, providers=[provider]
    )
    assert (
        ddo_transformation is not None
    ), "Creating asset transformation on-chain failed."
    print(
        f"[CONSUMER --> NEVERMINED] Publishing algorithm asset: {ddo_transformation.did}"
    )

    # Publish workflows
    workflow_metadata = example_metadata.workflow_ddo
    workflow_metadata["main"]["workflow"]["stages"][0]["input"][0]["id"] = ddo_data.did
    workflow_metadata["main"]["workflow"]["stages"][0]["transformation"][
        "id"
    ] = ddo_transformation.did

    ddo_workflow = nevermined.assets.create(
        workflow_metadata, consumer_acc, providers=[provider]
    )
    assert ddo_workflow is not None, "Creating asset workflow on-chain failed."
    print(f"[CONSUMER --> NEVERMINED] Publishing compute workflow: {ddo_workflow.did}")

    # Order computation
    service = ddo_compute.get_service(service_type=ServiceTypes.CLOUD_COMPUTE)
    service_agreement = ServiceAgreement.from_service_dict(service.as_dictionary())
    agreement_id = nevermined.assets.order(
        ddo_compute.did, service_agreement.index, consumer_acc
    )
    print(
        f"[CONSUMER --> PROVIDER] Requesting an agreement for compute to the data: {agreement_id}"
    )

    event = keeper.lock_reward_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Reward condition is not found"

    event = keeper.compute_execution_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Execution condition not found"

    # Execute workflow
    nevermined.assets.execute(
        agreement_id,
        ddo_compute.did,
        service_agreement.index,
        consumer_acc,
        ddo_workflow.did,
    )
    print("[CONSUMER --> PROVIDER] Requesting execution of the compute workflow")

    event = keeper.escrow_reward_condition.subscribe_condition_fulfilled(
        agreement_id, 60, None, (), wait=True
    )
    assert event is not None, "Escrow Reward condition not found"
    print("Workflow successfully executed")


if __name__ == "__main__":
    compute_example(verbose=False)
