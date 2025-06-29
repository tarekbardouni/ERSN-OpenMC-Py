readme.txt
The ERSN-OpenMC-Py is a graphical user interface specifically designed to streamline the use of the OpenMC code.
Our paper: ERSN-OpenMC-Py: A python-based open-source software for OpenMC Monte Carlo code. https://doi.org/10.1016/j.cpc.2024.109121

How to use the GUI to install openmc and prerequisistes under miniconda3
This tutorial is tested for ubuntu 23.04, miniconda3 and python 3.7 3.9 and 3.11
The new version 1.3 of ERSN-OpenMC-Py allows to post-process tallies created by combining up to 6 filters.
The version 1.3 of ERSN-OpenMC-Py allows to normalize tallies to cell volume, core power, unit lethargy and bin width.
Up to 5 filters are combined with MeshFilter.

Prof. Tarek El Bardouni and Doctor Mohamed Lahdour, University Abdelmalek Essaadi, Radiations and Nuclear Systems Team, Tetouan, Morocco

Emails: telbardouni@uae.ac.ma    and mohamedlahdour@gmail.com
URLs: 	https://github.com/tarekbardouni/ERSN-OpenMC-Py
		https://github.com/mohamedlahdour/ERSN-OpenMC-Py

		https://github.com/tarekbardouni/ERSN-OpenMC-Tutorials/blob/main/Install_OpenMC_Tutorial.mp4

A/ First make an update of your system and install the following packages if they don't exist:

	sudo apt update
	sudo apt upgrade

	sudo apt install g++ cmake libhdf5-dev libpng-dev

B/ Before running the GUI: install python3-pyqt5

	sudo apt install python3-pyqt5

or 

	sudo apt install pyqt5-dev pyqt5-dev-tools

C/ install git

	sudo apt install git

D/ extract the contents of the archive and run the application from its directory by executing :

	python3 gui.py


1. In the tab "get openmc" install miniconda3 and update its packages

2. close the gui

3. close and reopen the terminal

4. make sure the conda is activated

5. as pyqt5 is not yet installed under conda, if the GUI doesn't work, run it by executing :

	/usr/bin/python3 gui.py

insteade of : python3 gui.py

6. install prerequisites
	- Before installing prerequisites it is better to update miniconda on terminal or from the gui.
	- If the update frozes in "Solving environment" step an issue is:
		- delete the file : ~/.condarc
		- then set channel priority : conda config --set channel_priority flexible


	It's better to close the gui after prequisites installing is finished, then in a terminal activate the created openmc environment, 
         for example: conda activate openmc-py3.7
         
	If you can not run the gui because pyqt5 is not installed under conda, try the command in a terminal : 
         ==> Command : pip install pyqt5

         ==> If QtCore module cannot be loaded from PyQt5 force reinstall PyQt5 <==
         ==> Command : python3 -m pip install --upgrade --force-reinstall PyQt5 <==
            
         ==> For changes to take effect, close and re-open your current shell. <==
         

7. install openmc from the tab named "Install openmc: Inthernet connexion must be enabled

	If compiling openmc crashes repeat its installation. If the compiling still doesn't work properly because of old version of cmake, 
	reinstall cmake under conda by : 
		==> command : conda install cmake

8. download neutron data from the tab named "Get Cross Sections"

E/ runing openmc under the GUI

	Use the script bellow to lunch the gui to run openmc :

		conda activate openmc-py3.7

		export OPENMC_CROSS_SECTIONS=$HOME/Py-OpenMC-2024/data/endfb71_hdf5/cross_sections.xml      if endfb71_hdf5 has been downloaded

		python3 gui.py

	To run the two first commands automaticaly, each time the terminal is opened, add them to the .bashrc file.

	Note that the variable OPENMC_CROSS_SECTIONS must point to the correct path of downloaded cross sections data folder

F/ OpenMC could fail when installed under python 3.11
	You are using Python 3.11. The inspect (core library module) has changed since Python 3.7
	The following error could be accounterd while runing openmc under python3.11 environment:
 	File "/home/tarek/miniconda3/envs/openmc-py3.11/lib/python3.11/site-packages/uncertainties/core.py", line 583, in wrap
    	argspec = getargspec(f)
              ^^^^^^^^^^
	NameError: name 'getargspec' is not defined. Did you mean: 'argspec'?

	Prolem is resolved by replacing in file envs/openmc-py3.11/lib/python3.11/site-packages/uncertainties/core.py
	argspec = getargspec(f)
	by
	argspec = inspect.getfullargspec(f)


G/ Installing on Linux with Conda
	Once you have conda (Anaconda) installed on your system, OpenMC can be installed via the conda-forge channel.
	First, add the conda-forge channel with:
		conda config --add channels conda-forge
		conda config --set channel_priority strict
	
	Then create and activate a new conda enviroment called openmc-env (or whatever you wish) with OpenMC installed.
		conda create --name openmc-env openmc
		conda activate openmc-env
	
	You are now in a conda environment called openmc-env that has OpenMC installed.

	To run ERSN-OpenMC-Py you need to have pyqt5 installed on your environment. Install pyqt by runing:
		pip install pyqt5

	You need also to export OPENMC_CROSS_SECTIONS environment variable to point nuclear data directory:
		export OPENMC_CROSS_SECTIONS=$HOME/Your_Path_To_Data/data/endfb80_hdf5/cross_sections.xml
	(modify the Your_Path_To_Data)

	Then run :
		python3 gui.py

H/ License

This software is free software, you can redistribute it and / or modify it under the
terms of the GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version. For the complete
text of the license see the GPL-web page.
