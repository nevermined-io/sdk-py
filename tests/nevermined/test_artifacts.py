import os

from contracts_lib_py.web3_provider import Web3Provider
from web3 import Web3
from contracts_lib_py.web3.http_provider import CustomHTTPProvider
import pytest

from nevermined_sdk_py.config_provider import ConfigProvider
from nevermined_sdk_py.config import Config
from nevermined_sdk_py.nevermined.nevermined import Nevermined

INFURA_TOKEN = os.environ.get("INFURA_TOKEN")


@pytest.mark.parametrize("keeper_url,network_name", [
    [f"https://mainnet.infura.io/v3/{INFURA_TOKEN}", "mainnet"],
    [f"https://rinkeby.infura.io/v3/{INFURA_TOKEN}", "rinkeby"],
    ("http://localhost:8545", "spree"),
    ("https://rpc-mumbai.matic.today", "mumbai"),
    ("https://alfajores-forno.celo-testnet.org", "celo-alfajores"),
    ("https://baklava-forno.celo-testnet.org", "celo-baklava")
])
def test_artifact(keeper_url, network_name):
    options = {
        "keeper-contracts": {
            "keeper.url": keeper_url
        }
    }
    config = Config(options_dict=options)
    Web3Provider._web3 = Web3(CustomHTTPProvider(config.keeper_url))
    ConfigProvider.set_config(config)

    nevermined = Nevermined()
    assert nevermined.keeper.network_name == network_name