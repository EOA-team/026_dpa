"""Contains class to simulate M4MProc Windows Application """
import time
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)


class M4MProc_Application:
    """
    Class to simulate M4MProc which is only available as a Windows Application.
    M4mProc is a Beta Version of the Intacor Software. It integrates DROACOR and
    PARGE into one single processing software.

    The Processing Steps that are used in DPA are :
    1. Geocoding : Attaching a geographic coordinate system to the imagery
    2. Reflectance Retrieval : Converting the digital numbers to reflectance values (liighting and atmospheric correction)   
    3. Orthorectification : Uses a 3D terrain model to eliminate scale errors caused by uneven terrain and sensor tilt. 
    4. Mosaic : Stitch multiple images into a single image
    https://intacor.com/
    """