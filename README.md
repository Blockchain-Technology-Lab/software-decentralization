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

To collect data, execute the script `collect_commit_data` from the `data_collection` directory.
For example, you can use this command to do it from the root directory of the project:
```
python -m data_collection.collect_commit_data
```
Note that the script will clone the repositories of the projects listed in the `data_collection/repo_info.json` file 
to a new `data_collection/repos` subdirectory. 

To analyze the data, execute the `run.py` script from the root directory of the project:
```
python run.py
```


The script will generate an `output` directory with the results of the analysis (csv files and figures).

To configure the analysis, you can modify the [`config.yaml`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/config.yaml) file.