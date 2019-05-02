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

### Windows

To install CaliPy we recommend you to install conda first. Afterwards you can install all the required dependecies into a conda environment with the following command:

    conda env create -f environment.yml

Then run cali.py from the newly created environment.

### Ubuntu

Install some (?) dependecies with apt, then install calipy with:

    pip install

To start CaliPy run cali.py
