# software-decentralization
Tool that analyzes blockchain decentralization on the software layer 

## Installation

To install the software decentralization analysis tool, simply clone this GitHub repository:

    git clone https://github.com/Blockchain-Technology-Lab/software-decentralization.git

The tool is written in Python 3, therefore a Python 3 interpreter is required in order to run it locally.

The [requirements file](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/requirements.txt) lists 
the dependencies of the project.
Make sure you have all of them installed before running the scripts. To install
all of them in one go, run the following command from the root directory of the
project:

    python -m pip install -r requirements.txt

Replace `python` with your python version if necessary, e.g. `python3.9` (same for all following commands).


## Execution

To run the tool, simply execute the `run.py` script from the root directory of the project:

```
python run.py
```

If the script is executed for the first time, it will clone the repositories of the projects listed in the 
[`config.yaml`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/config.yaml)
file and extract data about their commit history. 

Some blockchains are implemented by more than one independent client (e.g. Bitcoin Cash has both `bitcoin-cash-node`
and `BCHUnlimited`). In these cases, the commit histories of all the client repositories configured for that
blockchain are merged into a single, chronologically ordered history before any metrics are calculated.
Decentralization is therefore measured at the level of the blockchain as a whole (across all of its client
implementations), rather than per individual repository. Note that Ethereum's execution and consensus clients are
treated separately (`ethereum_execution` and `ethereum_consensus`) for this purpose. See
the [Clients considered](#clients-considered) section below for the exact set of repositories that make up each
blockchain in the current configuration.

These data are then used to calculate various metrics that quantify the decentralization of the projects.

The script will generate an `output` directory with the results of the analysis,
organised in subdirectories depending on the type of output (data file or figure), 
contribution type (one of lines changed,  commits, or merge commits), 
contributor type (author or committer), and number of commits per sample window. 

To configure the analysis (e.g. change which repositories will be analysed or which metrics will be calculated), 
you can modify the [`config.yaml`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/config.yaml)
file. Repositories are listed under the name of the blockchain (ledger) they belong to; every repository listed
under the same blockchain has its commit history merged together, as described above. To add another repository to
a blockchain, list it under that blockchain in `config.yaml` and add its details (owner, default branch, and host -
`github` or `gitlab`) to
[`data_collection/repo_info.json`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/data_collection/repo_info.json).
Commenting out a repository in `config.yaml` excludes it from the analysis without needing to remove its entry from
`repo_info.json`.

## Clients considered

The table below lists, for each blockchain in the current
[`config.yaml`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/config.yaml)
configuration, the client repositories whose commit histories are merged together for that blockchain's
decentralization analysis.

| Blockchain | Clients |
|---|---|
| Bitcoin | [bitcoin](https://github.com/bitcoin/bitcoin) |
| Bitcoin Cash | [bitcoin-cash-node](https://github.com/bitcoin-cash-node/bitcoin-cash-node), [BCHUnlimited](https://gitlab.com/bitcoinunlimited/BCHUnlimited) |
| Cardano | [cardano-node](https://github.com/IntersectMBO/cardano-node) |
| Ethereum (consensus) | [lighthouse](https://github.com/sigp/lighthouse), [lodestar](https://github.com/ChainSafe/lodestar), [nimbus-eth2](https://github.com/status-im/nimbus-eth2), [prysm](https://github.com/OffchainLabs/prysm), [teku](https://github.com/Consensys/teku), [grandine](https://github.com/grandinetech/grandine) |
| Ethereum (execution) | [besu](https://github.com/hyperledger/besu), [erigon](https://github.com/ledgerwatch/erigon), [go-ethereum](https://github.com/ethereum/go-ethereum), [nethermind](https://github.com/NethermindEth/nethermind), [reth](https://github.com/paradigmxyz/reth) |
| Litecoin | [litecoin](https://github.com/litecoin-project/litecoin) |
| Polkadot | [polkadot-sdk](https://github.com/paritytech/polkadot-sdk) |
| Solana | [solana](https://github.com/solana-labs/solana) |
| Tezos | [tezos](https://gitlab.com/tezos/tezos) |
|XRPL | [rippled](https://github.com/XRPLF/rippled)|
| Zcash | [zcash](https://github.com/zcash/zcash), [zebra](https://github.com/ZcashFoundation/zebra) |
