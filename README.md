# Anonymize ULog Data
Ever wanted to remove sensitive information from your ULog such as GPS data or anonymize it? This is a solution for you!

This repository contains a script that can modify your GPS location data inside ULog to an arbitrary point.

## How to use

### Clone the repository
> **Note**, this repository relies on the submodule [`pyulog`](https://github.com/PX4/pyulog). So you must clone the repository with `--recursive` option to clone the submodules as well!

```bash
git clone https://github.com/junwoo091400/Anonymize_ULog_Data.git --recursive
```

### Activate python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install the pyulog in the venv
To use the pyulog properly (and install all of it's dependencies), the best option is to install the pyulog in the virtual environment. For which you can do the following:

```bash
cd pyulog/
python setup.py build install
cd ..
```

### 