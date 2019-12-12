import os
from math import log
from typing import List, NamedTuple, Optional

DECIMAL_PLACES = 2

GENESIS_TOKEN_UNITS = 2 * (10**9)  # 2B
GENESIS_TOKENS = GENESIS_TOKEN_UNITS * (10**DECIMAL_PLACES)  # 200B


class HathorSettings(NamedTuple):
    # Version byte of the address in P2PKH
    P2PKH_VERSION_BYTE: bytes

    # Version byte of the address in MultiSig
    MULTISIG_VERSION_BYTE: bytes

    # Name of the network: "mainnet", "testnet-alpha", "testnet-bravo", ...
    NETWORK_NAME: str

    # Initial bootstrap servers
    BOOTSTRAP_DNS: List[str] = []

    DECIMAL_PLACES: int = DECIMAL_PLACES

    # Genesis pre-mined tokens
    GENESIS_TOKEN_UNITS: int = GENESIS_TOKEN_UNITS

    GENESIS_TOKENS: int = GENESIS_TOKENS

    # To disable reward halving, one just have to set this to `None` and make sure
    # that INITIAL_TOKEN_UNITS_PER_BLOCK is equal to MINIMUM_TOKEN_UNITS_PER_BLOCK.
    BLOCKS_PER_HALVING: Optional[int] = 2 * 60 * 24 * 365  # 1051200, every 365 days

    INITIAL_TOKEN_UNITS_PER_BLOCK: int = 64
    INITIAL_TOKENS_PER_BLOCK: int = INITIAL_TOKEN_UNITS_PER_BLOCK * (10**DECIMAL_PLACES)

    MINIMUM_TOKEN_UNITS_PER_BLOCK: int = 8
    MINIMUM_TOKENS_PER_BLOCK: int = MINIMUM_TOKEN_UNITS_PER_BLOCK * (10**DECIMAL_PLACES)

    # Assume that: amount < minimum
    # But, amount = initial / (2**n), where n = number_of_halvings. Thus:
    #   initial / (2**n) < minimum
    #   initial / minimum < 2**n
    #   2**n > initial / minimum
    # Applying log to both sides:
    #   n > log2(initial / minimum)
    #   n > log2(initial) - log2(minimum)
    MAXIMUM_NUMBER_OF_HALVINGS: int = int(log(INITIAL_TOKEN_UNITS_PER_BLOCK, 2) -
                                          log(MINIMUM_TOKEN_UNITS_PER_BLOCK, 2))

    AVG_TIME_BETWEEN_BLOCKS: int = 30  # in seconds

    # Genesis pre-mined outputs
    # P2PKH HMcJymyctyhnWsWTXqhP9txDwgNZaMWf42
    #
    # To generate a new P2PKH script, run:
    # >>> from hathor.transaction.scripts import P2PKH
    # >>> import base58
    # >>> address = base58.b58decode('HMcJymyctyhnWsWTXqhP9txDwgNZaMWf42')
    # >>> P2PKH.create_output_script(address=address).hex()
    GENESIS_OUTPUT_SCRIPT: bytes = bytes.fromhex('76a914a584cf48b161e4a49223ed220df30037ab740e0088ac')

    # Weight of genesis and minimum weight of a tx/block
    MIN_BLOCK_WEIGHT: int = 21
    MIN_TX_WEIGHT: int = 14
    MIN_SHARE_WEIGHT: int = 21

    HATHOR_TOKEN_UID: bytes = b'\x00'

    # Maximum distance between two consecutive blocks (in seconds), except for genesis.
    # This prevent some DoS attacks exploiting the calculation of the score of a side chain.
    MAX_DISTANCE_BETWEEN_BLOCKS: int = 30*64  # P(t > T) = 1/e^30 = 9.35e-14

    # Number of blocks to be found with the same hash algorithm as `block`.
    # The bigger it is, the smaller the variance of the hash rate estimator is.
    BLOCK_DIFFICULTY_N_BLOCKS: int = 20

    # Maximum change in difficulty between consecutive blocks.
    #
    # The variance of the hash rate estimator is high when the hash rate is increasing
    # or decreasing. Many times it will overreact and increase/decrease the weight too
    # much. This limit is used to make the weight change more smooth.
    #
    # [msbrogli]
    # Why 0.25? I have some arguments in favor of 0.25 based on the models I've been studying.
    # But my arguments are not very solid. They may be good to compare 0.25 with 5.0 or higher values, but not to 0.50.
    # My best answer for now is that it will be rare to reach this limit due to the variance of the hash rate estimator
    # So, it will be reached only when the hash rate has really changed (increased or decreased). It also reduces
    # significantly the ripple effect overreacting to changes in the hash rate. For example, during my simulations
    # without a max_dw, when the hash rate increased from 2^20 to 2^30, the weight change was too big, and it took more
    # than 10 minutes to find the next block. After, it took so long that the weight change was reduced too much.
    # This ripple was amortized over time reaching the right value. Applying a max_dw, the ripple has been reduced.
    # Maybe 0.50 or 1.0 are good values as well.
    BLOCK_DIFFICULTY_MAX_DW: float = 0.25

    # Size limit in bytes for Block data field
    BLOCK_DATA_MAX_SIZE: int = 100

    # Number of subfolders in the storage folder (used in JSONStorage and CompactStorage)
    STORAGE_SUBFOLDERS: int = 256

    # Maximum level of the neighborhood graph generated by graphviz
    MAX_GRAPH_LEVEL: int = 3

    # Maximum difference between our latest timestamp and a peer's synced timestamp to consider
    # that the peer is synced (in seconds).
    P2P_SYNC_THRESHOLD: int = 60

    # Maximum number of opened threads that are solving POW for send tokens
    MAX_POW_THREADS: int = 5

    # The error tolerance, to allow small rounding errors in Python, when comparing weights,
    # accumulated weights, and scores
    # How to use:
    # if abs(w1 - w2) < WEIGHT_TOL:
    #     print('w1 and w2 are equal')

    # if w1 < w2 - WEIGHT_TOL:
    #     print('w1 is smaller than w2')

    # if w1 <= w2 + WEIGHT_TOL:
    #     print('w1 is smaller than or equal to w2')

    # if w1 > w2 + WEIGHT_TOL:
    #     print('w1 is greater than w2')

    # if w1 >= w2 - WEIGHT_TOL:
    #     print('w1 is greater than or equal to w2')
    WEIGHT_TOL: float = 1e-10

    # Maximum number of txs or blocks (each, not combined) to show on the dashboard
    MAX_DASHBOARD_COUNT: int = 15

    # Maximum number of txs or blocks returned by the '/transaction' endpoint
    MAX_TX_COUNT: int = 15

    # URL prefix where API is served, for instance: /v1a/status
    API_VERSION_PREFIX: str = 'v1a'

    # If should use stratum to resolve pow of transactions in send tokens resource
    SEND_TOKENS_STRATUM: bool = True

    # Maximum number of subscribed addresses per websocket connection
    WS_MAX_SUBS_ADDRS_CONN: int = 200000

    # Maximum number of subscribed addresses that do not have any outputs (also per websocket connection)
    WS_MAX_SUBS_ADDRS_EMPTY: int = 40

    # Whether miners are assumed to mine txs by default
    STRATUM_MINE_TXS_DEFAULT: bool = True

    # Percentage used to calculate the number of HTR that must be deposited when minting new tokens
    # The same percentage is used to calculate the number of HTR that must be withdraw when melting tokens
    # See for further information, see [rfc 0011-token-deposit].
    TOKEN_DEPOSIT_PERCENTAGE: float = 0.01

    # Array with the settings parameters that are used when calculating the settings hash
    P2P_SETTINGS_HASH_FIELDS: List[str] = [
        'P2PKH_VERSION_BYTE',
        'MULTISIG_VERSION_BYTE',
        'MIN_BLOCK_WEIGHT',
        'MIN_TX_WEIGHT',
        'BLOCK_DIFFICULTY_MAX_DW',
        'BLOCK_DATA_MAX_SIZE'
    ]

    # Maximum difference allowed between current time and a received tx timestamp (in seconds)
    MAX_FUTURE_TIMESTAMP_ALLOWED: int = 3600

    # Maximum number of peer connection attemps before stop retrying
    MAX_PEER_CONNECTION_ATTEMPS: int = 3

    # Multiplier for the value to increase the timestamp for the next retry moment to connect to the peer
    PEER_CONNECTION_RETRY_INTERVAL_MULTIPLIER: int = 5

    # Filepath of ca certificate file to generate connection certificates
    CA_FILEPATH: str = os.path.join(os.path.dirname(__file__), '../p2p/ca.crt')

    # Filepath of ca key file to sign connection certificates
    CA_KEY_FILEPATH: str = os.path.join(os.path.dirname(__file__), '../p2p/ca.key')

    # Timeout (in seconds) for the downloading deferred (in the downloader) when syncing two peers
    GET_DATA_TIMEOUT: int = 30

    # Maximum number of characters in a token name
    MAX_LENGTH_TOKEN_NAME: int = 30

    # Maximum number of characters in a token symbol
    MAX_LENGTH_TOKEN_SYMBOL: int = 5

    # Name of the Hathor token
    HATHOR_TOKEN_NAME: str = 'Hathor'

    # Symbol of the Hathor token
    HATHOR_TOKEN_SYMBOL: str = 'HTR'
