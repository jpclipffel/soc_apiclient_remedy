#!/bin/bash
#
# Autamatize soc_apiclient_remedy installation on a recalcitrant system.

PYTHON="/usr/bin/env python2.6"
ROOT_DIR="`dirname $0`"
PACKAGES_DIR="$ROOT_DIR/packages"
TOOLKIT_DIR="$ROOT_DIR/toolkit"
VENV_SCRIPT="$TOOLKIT_DIR/virtualenv.py"
SETUPTOOLS="setuptools-36.2.7"
SETUPTOOLS_ARCHIVE="$TOOLKIT_DIR/$SETUPTOOLS.zip"
SETUPTOOLS_UNZIP="$TOOLKIT_DIR/setuptools/"


venv_target=$1
if [[ -z "$venv_target" ]]; then echo "usage: `basename $0` </path/to/your/venv/>" >&2; exit 1; fi

echo "[*] creating virtualenv $1"
$PYTHON "$VENV_SCRIPT" --no-setuptools --no-pip --no-wheel --no-download "$venv_target"

echo "[*] activating virtualenv"
source "$venv_target/bin/activate"

echo "[*] unpacking and installing setuptools"
unzip "$SETUPTOOLS_ARCHIVE" -d "$SETUPTOOLS_UNZIP"
cwd=`pwd`
cd "$SETUPTOOLS_UNZIP/$SETUPTOOLS"
$PYTHON setup.py install
cd "$cwd"

echo "[*] installing dependencies"
cwd=`pwd`
cd "$PACKAGES_DIR"
python -m easy_install --no-deps *.tar.gz
cd "$cwd"

echo "[*] deactivating virtualenv"
deactivate

echo "[*] cleaning temporary files"
if [ -d "$SETUPTOOLS_UNZIP" ]; then rm -r "$SETUPTOOLS_UNZIP"; fi
find "$ROOT_DIR" -iname "*.pyc" -exec rm {} \;
