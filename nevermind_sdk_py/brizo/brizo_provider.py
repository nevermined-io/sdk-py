"""Brizo module."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from nevermind_sdk_py.brizo.brizo import Brizo


class BrizoProvider(object):
    """Provides a Brizo instance."""
    _brizo_class = Brizo

    @staticmethod
    def get_brizo():
        """ Get a Brizo instance."""
        return BrizoProvider._brizo_class()

    @staticmethod
    def set_brizo_class(brizo_class):
        """
         Set a Brizo class.

        :param brizo_class: Brizo-compatible class
        """
        BrizoProvider._brizo_class = brizo_class
