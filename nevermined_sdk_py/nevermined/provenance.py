import logging

from common_utils_py.did import did_to_id, id_to_did
from contracts_lib_py.web3_provider import Web3Provider
from eth_utils import add_0x_prefix


class Provenance:
    """Nevermined provenance class."""

    def __init__(self, keeper, config):
        self._keeper = keeper
        self._config = config

    def used(self, provenance_id, did, agent_id, activity_id, signature, account, attributes=None):
        """
        Implements the W3C PROV Usage action

        :param provenance_id: provenance ID
        :param did: Identifier of the entity created
        :param agent_id: Agent Identifier
        :param activity_id: Identifier of the activity creating the new entity
        :param signature: Signature (optional) provided by the agent involved
        :param attributes: Attributes associated with the action
        :param account: Account making the call

        :return: true if the provenance event was registered correctly

        """
        try:
            receipt = self._keeper.did_registry.used(
                self._convert_to_hex(provenance_id),
                self._convert_to_hex(did),
                self._convert_to_hex(agent_id),
                self._convert_to_hex(activity_id),
                signature, account, attributes)
            return bool(receipt and receipt.status == 1)
        except Exception as e:
            logging.critical(f'On-chain call error: {e}')
            return False

    def was_derived_from(self, provenance_id, new_entity_did, used_entity_did, agent_id,
                         activity_id, account, attributes=None):
        """
        Implements the W3C PROV Derivation action

        :param provenance_id: provenance ID
        :param new_entity_did: Identifier of the new entity derived
        :param used_entity_did: Identifier of the entity used to derive the new entity
        :param agent_id: Agent Identifier
        :param activity_id: Identifier of the activity creating the new entity
        :param attributes: Attributes associated with the action
        :param account: Account making the call

        :return: true if the provenance event was registered correctly
        """
        try:
            receipt = self._keeper.did_registry.was_derived_from(
                self._convert_to_hex(provenance_id),
                self._convert_to_hex(new_entity_did),
                self._convert_to_hex(used_entity_did),
                self._convert_to_hex(agent_id),
                self._convert_to_hex(activity_id),
                account, attributes)
            return bool(receipt and receipt.status == 1)
        except Exception as e:
            logging.critical(f'On-chain call error: {e}')
        return False

    def was_associated_with(self, provenance_id, did, agent_id, activity_id, account, attributes):
        """
        Implements the W3C PROV Association action

        :param provenance_id: provenance ID
        :param did: Identifier of the entity created
        :param agent_id: Agent Identifier
        :param activity_id: Identifier of the activity creating the new entity
        :param attributes: Attributes associated with the action
        :param account: Account making the call

        :return: true if the provenance event was registered correctly
        """
        try:
            receipt = self._keeper.did_registry.was_associated_with(
                self._convert_to_hex(provenance_id),
                self._convert_to_hex(did),
                self._convert_to_hex(agent_id),
                self._convert_to_hex(activity_id),
                account,
                attributes)
            return bool(receipt and receipt.status == 1)
        except Exception as e:
            logging.critical(f'On-chain call error: {e}')
            return False

    def acted_on_behalf(self, provenance_id, did, delegate_agent_id, responsible_agent_id,
                        activity_id, signature, account, attributes):
        """
        Implements the W3C PROV Association action

        :param provenance_id: provenance ID
        :param did: Identifier of the entity created
        :param delegate_agent_id: Delegate Agent Identifier
        :param responsible_agent_id:  Responsible Agent Identifier
        :param activity_id: Identifier of the activity creating the new entity
        :param attributes: Attributes associated with the action
        :param signature: Signature provided by the agent involved
        :param account: Account making the call

        :return: true if the provenance event was registered correctly
        """
        try:

            receipt = self._keeper.did_registry.acted_on_behalf(self._convert_to_hex(provenance_id),
                                                                self._convert_to_hex(did),
                                                                self._convert_to_hex(
                                                                    delegate_agent_id),
                                                                self._convert_to_hex(
                                                                    responsible_agent_id),
                                                                self._convert_to_hex(activity_id),
                                                                signature,
                                                                account, attributes)
            return bool(receipt and receipt.status == 1)
        except Exception as e:
            logging.critical(f'On-chain call error: {e}')
            return False

    def get_provenance_entry(self, provenance_id):
        """
        Fetch from the on-chain Provenance registry the information about one provenance event, given a provenance id

        :param provenance_id: provenance ID
        :return: information on-chain related with the provenance
        """
        provenance_entry = self._keeper.did_registry.get_provenance_entry(
            self._convert_to_hex(provenance_id))
        provenance_entry['did'] = id_to_did(provenance_entry['did'])
        provenance_entry['related_did'] = id_to_did(provenance_entry['related_did'])
        return provenance_entry

    def is_provenance_delegate(self, did, delegate):
        """
        Indicates if an address is a provenance delegate for a given DID
        :param did: Identifier of the asset
        :param delegate: delegate address of the delegate
        :return: true if the address is a provenance delegate
        """
        return self._keeper.did_registry.is_provenance_delegate(self._convert_to_hex(did), delegate)

    def add_did_provenance_delegate(self, did, delegated_address, account):
        """
        Adds an address as delegate for a given DID
        :param did: Identifier of the asset
        :param delegated_address: delegate address of the delegate
        :param account: Account making the call
        :return: true if the address is a provenance delegate
        """
        return self._keeper.did_registry.add_did_provenance_delegate(self._convert_to_hex(did),
                                                                     delegated_address, account)

    def remove_did_provenance_delegate(self, did, delegated_address, account):
        """
        Remove an address as delegate for a given DID
        :param did: Identifier of the asset
        :param delegated_address: delegate address of the delegate
        :param account: Account making the call
        :return: true if the address is a provenance delegate
        """
        return self._keeper.did_registry.remove_did_provenance_delegate(self._convert_to_hex(did),
                                                                        delegated_address, account)

    def get_provenance_owner(self, provenance_id):
        """
        Get the provenance owner.
        :param provenance_id: provenance ID

        :return: String with the address owning the provenance entry
        """
        return self._keeper.did_registry.get_provenance_owner(self._convert_to_hex(provenance_id))

    def get_did_provenance_events(self, did):
        """
        Search for ProvenanceAttributeRegistered events related with a specific DID
        :param did: Identifier of the asset

        :return: list of provenance events.
        """
        return self._keeper.did_registry.get_did_provenance_events(
            self._convert_to_hex(did))

    def get_did_provenance_methods_events(self, method, did):
        """
        Search for provenance methods (used, wasGeneratedBy, etc.) given a DID

        :param method: Provenance methods to fetch
        :param did: Identifier of the asset

        :return: list of provenance events.

        """
        return self._keeper.did_registry.get_provenance_method_events(method,
                                                                      self._convert_to_hex(did))

    @staticmethod
    def _convert_to_hex(i):
        if isinstance(i, str):
            if i.startswith('did:nv'):
                return Web3Provider.get_web3().toBytes(hexstr=add_0x_prefix(did_to_id(i)))
            else:
                return Web3Provider.get_web3().toBytes(hexstr=add_0x_prefix(i))
        elif isinstance(i, bytes):
            return i
        else:
            raise ValueError(f'The id {i} is not in a valid format.')
