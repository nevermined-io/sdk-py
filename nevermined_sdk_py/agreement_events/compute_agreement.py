import logging

from nevermined_sdk_py.gateway import GatewayProvider
from common_utils_py.did_resolver.did_resolver import DIDResolver
from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper


logger = logging.getLogger(__name__)


def execute_computation(event, agreement_id, did, service_agreement, consumer_account,
                        consume_callback, workflow_did):
    """
    Consumption of an asset after get the event call.

    :param event: AttributeDict with the event data.
    :param agreement_id: id of the agreement, hex str
    :param did: DID, str
    :param service_agreement: ServiceAgreement instance
    :param consumer_account: Account instance of the consumer
    :param consume_callback:
    :param secret_store_url: str URL of secret store node for retrieving decryption keys
    :param parity_url: str URL of parity client to use for secret store encrypt/decrypt
    :param downloads_path: str path to save downloaded files
    """
    logger.debug(f"consuming asset (agreementId {agreement_id}) after event {event}.")
    if consume_callback:
        gateway = GatewayProvider.get_gateway()
        consume_callback(
            agreement_id,
            DIDResolver(Keeper.get_instance().did_registry).resolve(did),
            DIDResolver(Keeper.get_instance().did_registry).resolve(workflow_did),
            consumer_account,
            gateway
        )
