# This is a Python program that will load a program for a Techman robot.
# This file is generated automatically using RoboDK Software.
# For more information, visit: https://robodk.com/

# ------------------------------------------------------
# Set the Robot IP or change as required
# You can also set the robot IP in RoboDK to generate and execute the program automatically:
#  1- Select "Connect" from the main menu
#  2- Select "Connect to Robot"
#  3- Enter the robot IP
ROBOT_IP = "127.0.0.1"


def MainProgram():
    # Run the program file (script file must be placed in the same folder)
    # The program file was originally saved here:
    # C:\Users\bjoer\devStudiet\MSc-MechAuto-NTNU\H26\MMA4002-DAM\3 Assignments\2 Product Architecture\robot_cell\tmflow_test\Omron_Remote//PickPlaceTest.script

    RunScript("PickPlaceTest")

    print("Main program completed")


