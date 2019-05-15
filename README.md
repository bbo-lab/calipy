CaliPy - Camera Calibration Application
=======================================

CaliPy is a Qt-based calibration application written in Python.

Currently supported calibration patterns:
  
  - [ChAruco Boards](https://docs.opencv.org/3.4.6/da/d13/tutorial_aruco_calibration.html)

Currently supported camera models:
 
  - [Pinhole Camera Model](https://docs.opencv.org/3.4.6/d9/d0c/group__calib3d.html#details)
  - [Omnidirectional Camera Model](https://docs.opencv.org/3.4.6/d3/ddc/group__ccalib.html)

Installation
------------

CaliPy depends on the following Python packages:

  - NumPy and SciPy
  - PyYAML
  - OpenCV incl. Contrib
  - ImageIO with FFMPEG support
  - Construct
  - PyQt5
  - PyQtGraph
  - PyInstaller (optional, for standalone build)
  
Current best practise is to install CaliPy with pip using its ```setup.py```. Once installed you can run calipy by 

Alterntivly if you have the ```pyinstaller``` package installed (i.e. via pip) you can turn CaliPy into a self contained executable with the followinf command:

    pyhton3 setup.py standalone

#### Conda

No longer recommended as conda's PyQt can not be bundled with PyInstaller.

You can install all the required dependencies into a conda environment with the following command:

    conda env create -f environment.yml

Then run cali.py from the newly created environment.
