#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
from os.path import join

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as history_file:
    history = history_file.read()
# Installed by pip install nevermined-sdk-py
# or pip install -e .
install_requirements = [
    'coloredlogs',
    'pyopenssl',
    'PyJWT',  # not jwt
    'PyYAML>=5.2',
    'common-utils-py==0.7.5',
    'contracts-lib-py==0.7.14',
    'nevermined-secret-store==0.1.1',
    'requests>=2.21.0',
    'deprecated',
    'pycryptodomex',
    'tqdm',
    'pytz'
    # web3 requires eth-abi, requests, and more,
    # so those will be installed too.
    # See https://github.com/ethereum/web3.py/blob/master/setup.py
]

# Required to run setup.py:
setup_requirements = ['pytest-runner', ]

test_requirements = [
    'coverage',
    'pylint',
    'pytest',
    'pytest-watch',
]

# Possibly required by developers of nevermined-sdk-py:
dev_requirements = [
    'bumpversion',
    'pkginfo',
    'twine',
    'watchdog',
]

docs_requirements = [
    'Sphinx',
    'sphinxcontrib-apidoc',
]

packages = []
for d, _, _ in os.walk('nevermined_sdk_py'):
    if os.path.exists(join(d, '__init__.py')):
        packages.append(d.replace(os.path.sep, '.'))

setup(
    author="nevermined-io",
    author_email='root@nevermined.io',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
    description="🐳 Nevermined Python SDK.",
    extras_require={
        'test': test_requirements,
        'dev': dev_requirements + test_requirements + docs_requirements,
        'docs': docs_requirements,
    },
    install_requires=install_requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='nevermined-sdk-py',
    name='nevermined-sdk-py',
    packages=packages,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/nevermined-io/sdk-py',
    version='0.10.4',
    zip_safe=False,
)
