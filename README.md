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
These data are then used to calculate various metrics that quantify the decentralization of the projects.

The script will generate an `output` directory with the results of the analysis,
organised in subdirectories depending on the type of output (data file or figure), 
contribution type (one of lines changed,  commits, or merge commits), 
contributor type (author or committer), and number of commits per sample window. 

To configure the analysis (e.g. change which repositories will be analysed or which metrics will be calculated), 
you can modify the [`config.yaml`](https://github.com/Blockchain-Technology-Lab/software-decentralization/blob/main/config.yaml)
file.