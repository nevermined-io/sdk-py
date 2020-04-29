import logging

from contracts_lib_py import Keeper


class NevermindKeeper(Keeper):

    @staticmethod
    def get_instance(artifacts_path=None, contract_names=None):
        return NevermindKeeper(artifacts_path)

    def get_condition_name_by_address(self, address):
        """Return the condition name for a given address."""
        if self.lock_reward_condition.address == address:
            return 'lockReward'
        elif self.access_secret_store_condition.address == address:
            return 'accessSecretStore'
        elif self.compute_execution_condition.address == address:
            return 'execCompute'
        elif self.escrow_reward_condition.address == address:
            return 'escrowReward'
        else:
            logging.error(f'The current address {address} is not a condition address')