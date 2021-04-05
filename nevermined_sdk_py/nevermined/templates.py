import logging

logger = logging.getLogger(__name__)


class Templates:
    """Nevermined templates class."""

    def __init__(self, keeper, config):
        self._keeper = keeper
        self._config = config
        self.access_template_id = self._keeper.access_template.address

    def propose(self, template_address, account):
        """
        Propose a new template.

        :param template_address: Address of the template contract, str
        :param account: account proposing the template, Account
        :return: bool
        """
        try:
            proposed = self._keeper.template_manager.propose_template(template_address, account)
            return proposed
        except ValueError as err:
            template_values = self._keeper.template_manager.get_template(template_address)
            if not template_values:
                logger.warning(f'Propose template failed: {err}')
                return False

            if template_values.state != 1:
                logger.warning(
                    f'Propose template failed, current state is set to {template_values.state}')
                return False

            return True

    def approve(self, template_address, account):
        """
        Approve a template already proposed. The account needs to be owner of the templateManager
        contract to be able of approve the template.

        :param template_address: Address of the template contract, str
        :param account: account approving the template, Account
        :return: bool
        """
        try:
            approved = self._keeper.template_manager.approve_template(template_address, account)
            return approved
        except ValueError as err:
            template_values = self._keeper.template_manager.get_template(template_address)
            if not template_values:
                logger.warning(f'Approve template failed: {err}')
                return False

            if template_values.state == 1:
                logger.warning(f'Approve template failed, this template is '
                               f'currently in "proposed" state.')
                return False

            if template_values.state == 3:
                logger.warning(f'Approve template failed, this template appears to be '
                               f'revoked.')
                return False

            if template_values.state == 2:
                return True

            return False

    def revoke(self, template_address, account):
        """
        Revoke a template already approved. The account needs to be owner of the templateManager
        contract to be able of revoke the template.

        :param template_address: Address of the template contract, str
        :param account: account revoking the template, Account
        :return: bool
        """
        try:
            revoked = self._keeper.template_manager.revoke_template(template_address, account)
            return revoked
        except ValueError as err:
            template_values = self._keeper.template_manager.get_template(template_address)
            if not template_values:
                logger.warning(f'Cannot revoke template since it does not exist: {err}')
                return False

            logger.warning(f'Only template admin or owner can revoke a template: {err}')
            return False

    def get_list_size(self):
        """
        Return the number of templates approved.
        """
        return self._keeper.template_manager.get_num_templates()

    def get_template(self, template_id):
        """
        Get the template for a given template id.

        :param template_id: id of the template, str
        """
        return self._keeper.template_manager.get_template(template_id)

    def is_template_approved(self, template_address):
        """
        Return true is the template is approved
        :param template_address: Address of the template contract, str
        """
        return self._keeper.template_manager.is_template_approved(template_address)