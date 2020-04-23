#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from web3 import Web3
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
assert w3.isConnected().
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
filter = w3.eth.filter('pending')
logs = w3.eth.getFilterLogs(filter.filter_id)
print("Connecting web3 through a websocket connection.")
