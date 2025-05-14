# keitai-tools

Utility to help process raw Java game dump folders from Japanese feature phones (keitai).
This is the script you use after dumping internal memory of a keitai to have games be formatted in a way that they can be played on a DoCoMo emulator (DoJa or Star).

This tool supports parsing `FJJAM.DB` files found on certain phone models. These files require reconstructing JAM files from the database.

## Prerequisites

Requires **Python 3.10+**

Set up a virtual environment and install dependencies using `pip`.

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install construct scsu
```

### Windows

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install construct scsu
```

## Usage

```
usage: kttools.py [-h] [--verbose] top_folder_directory

Process a directory containing a raw top level folder with keitai apps. Outputs files in emulator import ready format.

positional arguments:
  top_folder_directory  The top folder directory containing the keitai apps.

options:
  -h, --help            show this help message and exit
  --verbose             Print more information about conversion process.
```
