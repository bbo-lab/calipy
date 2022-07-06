CaliPy - Camera Calibration Application
=======================================

CaliPy is a Qt-based calibration application written in Python. It uses OpenCV and Bbolab/Calibcam in the background to perform camera calibration.

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
  - OpenCV
  - ImageIO with FFMPEG support
  - Construct
  - PyQt5
  - PyQtGraph
  - Bbolab/Calibcam
  - Bbolab/Calibcamlib
  - Joblib
  - Autograd
  - PyInstaller (optional, for standalone build)

Current best practise is to install CaliPy with pip using its ```setup.py```, i.e. with ```pip install .``` inside the repository folder. Once installed you can run ```calipy``` from the command line to start the application. On Linux you should also be able to start it from its startmenu entry.

Alterntively if you have the ```pyinstaller``` package installed (i.e. via pip) you can turn CaliPy into a self-contained executable with the following command:

    python3 setup.py standalone

The resulting ```CaliPy``` folder inside the ```dist``` subfolder can then be packed and distributed without the need to install any dependencies.

#### Conda

_No longer recommended as conda's PyQt can not be bundled with PyInstaller._

You can install all the required dependencies into a conda environment with the following command:

    conda env create -f environment.yml

Then run cali.py from the newly created environment.

Usage
-----

1. Add cameras with appropriate identifiers in the 'Cameras' dock on the top left side of the window.
2. In the 'Sources' dock, add a session and add a recording for each one of the cameras to the session. Multiple such sessions can be added.
3. Enter the ChAruco board parameters used in the session in the 'Detection' dock on right side of the window.
4. 'Run Detection' to find the ChAruco and Square corners. After the detection is done, corners are displayed.
5. Select one of the camera models in the 'Calibration' dock and press 'Calibrate Cameras'. This calibrates the cameras individually.
After the calibration is done, projected corners are displayed.
6. Run 'Calibrate System' to perform multi calibration, this optimises the intrinsic and extrinsic parameters of the cameras together.
After the calibration is done, projected corners are displayed.
7. Select the calibration results to be displayed in  the right bottom side of the window.


Format
------

Use ```File > Save..``` to save the session and the added sources as a ```.system.yml``` file. The session can be reopened by selecting it under ```File > Open..```.

Use ```Result > Save..``` to save the result, detections and calibrations, as a ```.result.pickle``` file. The result can be reloaded by selecting it under ```Result > Load..```.


