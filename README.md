[![banner](https://raw.githubusercontent.com/keyko-io/assets/master/images/logo/small/keyko_logo@2x-100.jpg)](https://keyko.io)

# Python API for Nevermind Data platform

> 🦑 Python SDK for connecting with Nevermind Data Platform
> [keyko.io](https://keyko.io)

[![PyPI](https://img.shields.io/pypi/v/nevermind-sdk-py.svg)](https://pypi.org/project/nevermind-sdk-py/)

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

Squid-py include the methods to make easy the connection with contracts deployed in different networks.
This repository include also the methods to encrypt and decrypt information using the Parity Secret Store.

## Prerequisites

Python 3.6

## Quick-start

Install Squid:

```
pip install nevermind-sdk-py
```

### Usage:

```python
import os
import time

from nevermind_sdk_py import (
    Nevermind,
    ConfigProvider,
    Config,
    Metadata,
    Account
)

ConfigProvider.set_config(Config('config.ini'))
# Make a new instance of Nevermind
nevermind = Nevermind() # or Nevermind(Config('config.ini'))
config = nevermind.config
# make account instance, assuming the ethereum account and password are set 
# in the config file `config.ini`
account = nevermind.accounts.list()[0]
# or 
account = Account(config.parity_address, config.parity_password)

# PUBLISHER
# Let's start by registering an asset in the Nevermind network
metadata = Metadata.get_example()

# consume and service endpoints require `gateway.url` is set in the config file
# or passed to Nevermind instance in the config_dict.
# define the services to include in the new asset DDO

ddo = nevermind.assets.create(metadata, account)

# Now we have an asset registered, we can verify it exists by resolving the did
_ddo = nevermind.assets.resolve(ddo.did)
# ddo and _ddo should be identical

# CONSUMER
# search for assets
asset_ddo = nevermind.assets.search('Nevermind protocol')[0]
# Need some ocean tokens to be able to order assets
nevermind.accounts.request_tokens(account, 10)

# Start the purchase/consume request. This will automatically make a payment from the specified account.
consumer_account = nevermind.accounts.list()[1]
service_agreement_id = nevermind.assets.order(asset_ddo.did, 0, consumer_account)

# after a short wait (seconds to minutes) the asset data files should be available in the `downloads.path` defined in config
# wait a bit to let things happen
time.sleep(20)

# Asset files are saved in a folder named after the asset id
dataset_dir = os.path.join(nevermind.config.downloads_path, f'datafile.{asset_ddo.asset_id}.0')
if os.path.exists(dataset_dir):
    print('asset files downloaded: {}'.format(os.listdir(dataset_dir)))

```

## Configuration

```python
config_dict = {
    'keeper-contracts': {
        # Point to an Ethereum RPC client. Note that Squid learns the name of the network to work with from this client.
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
        'storage.path': 'squid_py.db',
        # Where to store downloaded asset files
        'downloads.path': 'consume-downloads'
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

1. Create the local testing environment using [nevermind-tools](https://github.com/keyko-io/nevermind-tools). Once cloned that repository, you can start the cluster running:

    ```
    ./start_nevermind.sh --latest --no-gateway --no-common --local-spree-node
    ```

    It runs a Nevermind Metadata node and an Ethereum RPC client. For details, read `docker-compose.yml`.

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