#!/bin/bash
    
# This script installs OpenMC, its Python API, and all necessary dependencies
# into a conda environment. Because it uses compilers and CMake from the
# Anaconda repository, it's not necessary to have those installed on your
# system. However, at a minimum, you do need to have 'make' installed as well as
# a linker. To get the OpenMC git repository, you'll need git installed as
# well. On Debian derivatives, you can install all of these with:
#
# sudo apt install -y make binutils git

set -e

#===============================================================================
# INSTALLATION OPTIONS
INSTALL_CONDA=$1
DOWNLOAD_CONDA=$2
SCRIPT=$3
CONDA_URL=$4
UPDATE_CONDA=$5
ENVNAME=${6}                               # conda environment name
conda=${7}
CONDA_DIR=${8}
INSTALL_OPENMC=${9}
INSTALL_PQTY=${10}

#===============================================================================
#                     Download and install miniconda
#===============================================================================
if [[ $INSTALL_CONDA == yes ]]; then
    if [[ $DOWNLOAD_CONDA == yes ]]; then
        if [[ -f "$SCRIPT" ]]; then
            echo "#########     $SCRIPT script already exists !     #########"
        else        
            wget $CONDA_URL
        fi
    fi
    echo "#########     conda3 will be installed !     #########"
    bash $SCRIPT -b 
    # $HOME/anaconda3/bin/conda update -y -n base -c defaults conda
    $conda init bash
    source ~/.bashrc
    if [ $? -eq 0 ]; then 
        if [[ $UPDATE_CONDA == yes ]]; then
            # source ~/.bashrc
            $conda update -y -n base -c defaults conda
        else
            echo "#########     An update of anaconda may be required !     #########"
        fi  
    else
        echo "#########     Check if anaconda has been installed successfuly !     #########"
    fi
    echo "==> For changes to take effect, close and re-open your current shell. <=="
else
    $conda init bash
    source ~/.bashrc
    if [ $? -eq 0 ]; then 
        if [[ $UPDATE_CONDA == yes ]]; then
            # source ~/.bashrc
            $conda update -y -n base -c defaults conda
        else
            echo "#########     An update of anaconda may be required !     #########"
        fi  
    else
        echo "#########     Check if anaconda has been installed successfuly !     #########"
    fi
    echo "==> For changes to take effect, close and re-open your current shell. <=="
fi
echo
if [[ $INSTALL_PQTY == yes ]]; then
    if [[ -f "$CONDA_DIR/etc/profile.d/conda.sh" ]]; then
        source ~/.bashrc
        . $CONDA_DIR/etc/profile.d/conda.sh
        conda activate
        if [[ -z "$(conda list|grep pyqt)" ]]; then
            echo
            echo "#########               PyQT5 will be installed !           #########"
            #conda install -y pyqt
            pip install pyqt5
            echo
            echo "==> If QtCore module cannot be loaded from PyQt5 force reinstall PyQt5 <=="
            echo "==> Command : python3 -m pip install --upgrade --force-reinstall PyQt5 <=="
            echo
            echo "==> For changes to take effect, close and re-open your current shell. <=="
        fi
    fi
fi

#===============================================================================
#                            OpenMC Installation
#===============================================================================

if [[ $INSTALL_OPENMC == yes ]]; then
    # Make sure conda is activated
    . $CONDA_DIR/etc/profile.d/conda.sh
    source ~/.bashrc
    # Create new Python environment to install everything into
    if [[ ! "$CONDA_DIR/envs/$ENVNAME" || ! -d "$CONDA_DIR/envs/$ENVNAME" ]]; then
        conda config --add channels conda-forge
        conda config --set channel_priority strict
        conda create --name $ENVNAME -y openmc
        conda activate $ENVNAME
    else
        conda activate $ENVNAME
    fi
    if [[ ! -f "$CONDA_DIR/envs/$ENVNAME/bin/qmake" ]]; then    
        pip install pyqt5
    fi
fi
