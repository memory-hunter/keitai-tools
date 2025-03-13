# keitai-tools

Utiliy to help process raw Java game dump folders from Japanese feature phones (keitai).
This is the script you use after dumping internal memory of a keitai to have games be formatted in a way that they can be played on a DoCoMo emulator (DoJa or Star).

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
