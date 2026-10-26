# Omron_DAM: RoboDK's Omron (TMflow .flow zip) post processor, copied unchanged except that it does
# not open Explorer / the text file after writing (SHOW_PROGRAM_ZIP/TXT = False).
# bench_cell_v3.py / bench_cell_v4.py copy this file into C:/RoboDK/Posts/ when it is missing or out of date.
#
# -*- coding: UTF-8 -*-
# Copyright 2015-2026 - RoboDK - https://robodk.com/
#
# This is a compiled post processor. Please contact us at info@robodk.com if you need access to the source code of this post processor.
#
# More information about this post processor:
#     https://robodk.com/post/Omron
#
# More information about RoboDK Post Processors and Offline Programming:
#     https://robodk.com/doc/en/Post-Processors.html#SelectPost
#     https://robodk.com/doc/en/PythonAPI/postprocessor.html
# ----------------------------------------------------
#--------------
# Description
# The Omron post processor generates TMFlow (.flow) code compatible with Omron robotic controllers.
#
#
# Supported Controllers
#
#--------------

import sys
import os

import math
from robodk import *

# Detect Python version and post processor path
print("Using Python version: " + str(sys.version_info))
print("RoboDK Post Processor: " + __file__)

# Load the post processor from libspp
try:
    from libspp.Omron import RobotPost as MainPost

except Exception as e:
    import traceback
    msg = "Invalid Python version or post processor not found. Make sure to download the latest version of RoboDK."
    msg += "\nSelect Tools-Options-Python and select a supported Python version"
    msg += "\nThis script was executed using Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro)
    msg += "\nInformation about the error:\n" + repr(e)
    msg += "\n" + traceback.format_exc()
    print(msg)
    raise Exception(msg)

class RobotPost(MainPost):

    # ------------------------ Customize your RoboDK post processor using the following variables ------------------------

    # Maximum number of lines per program. If the number of lines is exceeded, the program will be executed step by step by RoboDK
    MAX_LINES_X_PROG = 1e9  # 5000

    # Show zip file on program generation
    SHOW_PROGRAM_ZIP = False

    # Show text file on program generation
    SHOW_PROGRAM_TXT = False

    # Set to True to skip comments
    SKIP_COMMENTS = False

    # Include subprograms in the same program
    INCLUDE_SUBPROGS = True

    # Use the robot base or a reference frame
    USE_ROBOT_BASE = False

    # Use targets as offsets
    USE_TARGET_OFFSETS = False

    # Number of instructions to stack vertically before creating a new column
    VERTICAL_INS = 8

    # Set the maximum speed in DEG/s (percentage speed will be calculated accordingly)
    MAX_SPEED_DEGS = 185

    # Set the maximum speed in MM/s (percentage speed will be calculated accordingly)
    MAX_SPEED_MMS = 1200

    # Set default Point Speed Percentage (PSPercentage)
    PSPERCENTAGE = 100

    # Set default Point Speed Time To Top Speed (PSTTTS)
    PSTTTS = 150

    # Flag compute joint acceleration (this would not be requiered if RDK would generate speed before acceleration)
    COMPUTE_JOINT_ACCEL = None

    # Enable Point Speed Time To Top Speed (PSTTTSOF)
    PSTTTSOF = "ON"

    # Set default LineABS
    LINE_ABS = "ON"

    # Set default Linear Speed Percentage (LSPercentage)
    LSPERCENTAGE = 100

    # Set default Linear Speed A Velocity (LSAVelocity)
    LSAVELOCITY = 250

    # Set default Linear Speed Time To Top Speed (LSTTTS)
    LSTTTS = 300

    # Set default payload for the robot movements
    OBJECT_PAYLOAD = 2

    # Set to True to adjust speeds for a remote TCP setup
    REMOTE_TCP_SPEED = False

    # Flag compute linear acceleration (this would not be requiered if RDK would generate speed before acceleration)
    COMPUTE_LINEAR_ACCEL = None

    # Set default rounding (radius in mm), set to -1 for accurate movements (point to point)
    ROUNDING_MM = 1

    # Set default blending mode for linear and circular movement (False = Pourcentage True = Radius)
    USE_RADIUS_BLENDING = False

    # Flag to include all init messages in one Display Node
    INIT_MESSAGE = None

    # Set the default password (5 chars minimum)
    # Warning: if set to None, the password will match the program name (filled with numbers to reach a minimum of 8 characters)
    # Warning: if the password is changed, TMFlow may not accept it and ask for a new password
    SET_PASSWORD = 'robodk1234'

    # Set to true to ask the user for a password
    ASK_PASSWORD = False

    # Set to 0 to not save a ZIP file
    # Set to 1 to save a zip file using TMExportZip
    # Set to 2 to save a zip file without using TMExportZip
    #ZIP_TYPE = 0
    ZIP_TYPE = 1
    #ZIP_TYPE = 2

    # --------------------------------------------------------------------------------------------------------------------

    pass

if __name__== "__main__":
    from libspp.Omron import test_post
    test_post()

