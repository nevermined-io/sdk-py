[![banner](https://raw.githubusercontent.com/nevermined-io/assets/main/images/logo/banner_logo.png)](https://nevermined.io)

# Python API for Nevermined Data platform

> Python SDK for connecting with Nevermined Data Platform
> [nevermined.io](https://nevermined.io)

[![PyPI](https://img.shields.io/pypi/v/nevermined-sdk-py.svg)](https://pypi.org/project/nevermined-sdk-py/)
[![Python package](https://github.com/nevermined-io/sdk-py/workflows/Python%20package/badge.svg)](https://github.com/nevermined-io/sdk-py/actions)
---

## Table of Contents

  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Quick-start](#quick-start)
     - [Usage:](#usage)
  - [Configuration](#configuration)
  - [Development](#development)
        - [Testing](#testing)
        - [New Version / New Release](#new-version-new-release)
  - [License](#license)

---

## Features

Sdk-py include the methods to make easy the connection with contracts deployed in different networks.
This repository include also the methods to encrypt and decrypt information using the Parity Secret Store.

## Prerequisites

Python 3.6

To use the data transfer proof, a C++ library is required:

```bash
git clone https://github.com/nevermined-io/rapidsnark
cd rapidsnark
git submodule update --init --recursive
sh ./scripts/install-linux.sh
```

## Quick-start

Install sdk:

```
pip install nevermined-sdk-py
```

### Usage:

```python
import os
import time

from nevermined_sdk_py import (
    Nevermined,
    ConfigProvider,
    Config,
    Metadata,
    Account
)

ConfigProvider.set_config(Config('config.ini'))
# Make a new instance of Nevermined
nevermined = Nevermined() # or Nevermined(Config('config.ini'))
config = nevermined.config
# make account instance, assuming the ethereum account and password are set 
# in the config file `config.ini`
account = nevermined.accounts.list()[0]
# or 
account = Account(config.parity_address, config.parity_password)

# PUBLISHER
# Let's start by registering an asset in the Nevermined network
metadata = Metadata.get_example()

# access and service endpoints require `gateway.url` is set in the config file
# or passed to Nevermined instance in the config_dict.
# define the services to include in the new asset DDO

ddo = nevermined.assets.create(metadata, account)

# Now we have an asset registered, we can verify it exists by resolving the did
_ddo = nevermined.assets.resolve(ddo.did)
# ddo and _ddo should be identical

# CONSUMER
# search for assets
asset_ddo = nevermined.assets.search('Nevermined protocol')[0]
# Need some ocean tokens to be able to order assets
nevermined.accounts.request_tokens(account, 10)

# Start the purchase/access request. This will automatically make a payment from the specified account.
consumer_account = nevermined.accounts.list()[1]
service_agreement_id = nevermined.assets.order(asset_ddo.did, 0, consumer_account)

# after a short wait (seconds to minutes) the asset data files should be available in the `downloads.path` defined in config
# wait a bit to let things happen
time.sleep(20)

# Asset files are saved in a folder named after the asset id
dataset_dir = os.path.join(nevermined.config.downloads_path, f'datafile.{asset_ddo.asset_id}.0')
if os.path.exists(dataset_dir):
    print('asset files downloaded: {}'.format(os.listdir(dataset_dir)))

```

## Configuration

```python
config_dict = {
    'keeper-contracts': {
        # Point to an Ethereum RPC client. Note that sdk learns the name of the network to work with from this client.
        'keeper.url': 'http://localhost:8545',
        # Specify the keeper contracts artifacts folder (has the smart contracts definitions json files). When you
        # install the package, the artifacts are automatically picked up from the `keeper-contracts` Python
        # dependency unless you are using a local ethereum network.
        'keeper.path': 'artifacts',
        'secret_store.url': 'http://localhost:12001',
        'parity.url': 'http://localhost:8545',
        'parity.address': '',
        'parity.password': '',

    },
    'resources': {
        # Metadata is the metadata store. It stores the assets DDO/DID-document
        'metadata.url': 'http://localhost:5000',
        # Gateway is the publisher's agent. It serves purchase and requests for both data access and compute services
        'gateway.url': 'http://localhost:8030',
        # points to the local database file used for storing temporary information (for instance, pending service agreements).
        'storage.path': 'sdk.db',
        # Where to store downloaded asset files
        'downloads.path': 'access-downloads'
    }
}

```

In addition to the configuration file, you may use the following environment variables (override the corresponding configuration file values):

- KEEPER_PATH
- KEEPER_URL
- GAS_LIMIT
- METADATA_URL

## Development

1. Set up a virtual environment

    ```bash
    virtualenv venv -p python3.6
    source venv/bin/activate 
    ```

1. Install requirements

    ```
    pip install -r requirements_dev.txt
    ```

1. Create the local testing environment using [nevermined-tools](https://github.com/nevermined-io/tools). Once cloned that repository, you can start the cluster running:

    ```
    ./start_nevermined.sh --latest --no-gateway --no-common --local-spree-node
    ```

    It runs a Nevermined Metadata node and an Ethereum RPC client. For details, read `docker-compose.yml`.

1. Create local configuration file

    ```
    cp config.ini config_local.ini
    ```

   `config_local.ini` is used by unit tests.

1. Copy keeper artifacts

    A bash script is available to copy keeper artifacts into this file directly from a running docker image. This script needs to run in the root of the project.
    The script waits until the keeper contracts are deployed, and then copies the artifacts.

    ```
    ./scripts/wait_for_migration_and_extract_keeper_artifacts.sh
    ```

    The artifacts contain the addresses of all the deployed contracts and their ABI definitions required to interact with them.


#### Testing

Automatic tests are setup via Github actions
Our test use pytest framework.

```bash
export PARITY_ADDRESS=0x00bd138abd70e2f00903268f3db08f2d25677c9e
export PARITY_PASSWORD=node0
export PARITY_KEYFILE=tests/resources/data/key_file_2.json
export PARITY_ADDRESS1=0x068ed00cf0441e4829d9784fcbe7b9e26d4bd8d0
export PARITY_PASSWORD1=secret
export PARITY_KEYFILE1=tests/resources/data/key_file_1.json
```

#### New Version / New Release

See [RELEASE_PROCESS.md](RELEASE_PROCESS.md)

##Attribution
This project is based in the [Ocean Protocol Squid-py](https://github.com/oceanprotocol/squid-py). It keeps the same Apache v2 License and adds some improvements.


## License

```text
Copyright 2020 Keyko GmbH.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
