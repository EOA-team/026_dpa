"""
APX-20 Trajectory Data Scraper Module

A web scraper tool that uses Microsoft Edge with Selenium to fetch trajectory data
from the Applanix APX-20 GNSS-Inertial sensor connected to the Data Acquisition Unit
(DAU) onboard computer.

Connection Requirements
-----------------------
- APX-20 web interface accessible at: http://192.168.168.100/
- DAU onboard computer must be connected to APX-20
- DAU must be connected to drone during operation

Functionality
-------------
- Automatically detects APX-20 availability via network reachability check
- Downloads all available T04 trajectory files from APX-20 web interface
- Saves downloaded files to D:/HySpexAir/TrajectoryData/
- Cleans up downloaded files from APX-20 to free storage space
- Provides detailed logging of all download operations

Author: Pascal Ackermann
Branch: feature/4-rawdata_to_hd
"""

