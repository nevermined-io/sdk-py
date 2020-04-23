#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from inspect import signature

from contracts_lib_py.web3_provider import Web3Provider


@contextmanager
def inject_dependencies(klass, *args, **kwargs):
    dependencies = kwargs.pop('dependencies', {})
    if 'dependencies' in signature(klass).parameters:
        kwargs['dependencies'] = dependencies

    to_restore = []

    def patch_provider(_object, _property, mock):
        to_restore.append((_object, _property, getattr(_object, _property)))
        setattr(_object, _property, mock)

    def maybe_patch_provider(_object, _property, name):
        if name in dependencies:
            patch_provider(_object, _property, dependencies[name])

    maybe_patch_provider(Web3Provider, '_web3', 'web3')
    try:
        yield klass(*args, **kwargs)
    finally:
        for (_object, _property, value) in to_restore:
            setattr(_object, _property, value)
