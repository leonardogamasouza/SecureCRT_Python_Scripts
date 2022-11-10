# $language = "Python"
# $interface = "1.0"
from __future__ import unicode_literals
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import re
import difflib

def main():
    crt.Screen.Synchronous = True
    # Tells CRT Screen to ignore case. Useful since device names do not use a standard case!
    crt.Screen.IgnoreCase = True
    # Select whether this is a PRE or POST test. 
    test_type = crt.Dialog.Prompt("Please select test option:\n 1. PRE Test\n 2. POST Test",
                                  "Please Select Test Type", "1", False)

    # If cancel is pressed there will be no input and script will exit
    if test_type == "":
        crt.Dialog.MessageBox("Script Cancelled!")
        return

    number_device = crt.Dialog.Prompt("Please select test option:\n 1. Single Device Test\n 2. Multiple Device",
                                      "Please Select Test Type", "2", False)

    if number_device == "2":
        crt.Dialog.MessageBox("Conecte na GESA primeiro!")
        use_jump = "1"
        # If cancel is pressed there will be no input and script will exit
        if use_jump == "1":
            # Process Devices - Call multi_device_jump()
            multi_device_jump(test_type)
        elif use_jump == "2":
            return
        elif use_jump == "":
            crt.Dialog.MessageBox("Script Cancelled!")
            return
    if number_device == "1":
        use_jump = crt.Dialog.Prompt("Will this test use a jump host? (Ex. GESA):\n 1. Yes\n 2. No",
                                     "Please Select Yes or No", "1", False)
        # Test type input is turned all upper case
        use_jump = use_jump.upper()

        if use_jump == "1":
            # Process Devices - Call multi_device_jump()
            single_device_jump(test_type)
        elif use_jump == "2":
            single_device(test_type)
        elif use_jump == "":
            crt.Dialog.MessageBox("Script Cancelled!")
    elif number_device == "":
        crt.Dialog.MessageBox("Script Cancelled!")

    # After all devices are worked through the user will be alerted that the script is complete
    # Connection to GESA will remain up
    crt.Dialog.MessageBox("COMPLETE!")
    crt.Screen.Synchronous = False


def multi_device_jump(test_type):
    new_device = True

    # Opens dialog to select device list text file
    device_types = crt.Dialog.Prompt("Will you have more than one type of device? (Junos, IOS, NX-OS, etc.):\n 1. Yes\n 2. No",
                                     "Please Select Yes or No", "2", False)

    if device_types == "1":
        crt.Dialog.MessageBox("Must have separate device list and command list for each group of devices!")

    while new_device == True:

        # Opens dialog to select device list text file
        device_list = open(crt.Dialog.FileOpenDialog(title="Please select a Device List text file",
                                                 filter="Text Files (*.txt)|*.txt||")).read().splitlines()
        # Remove any blank lines
        device_list = filter(None, device_list)

        # Remove white space from entries...device names cannot contain white space
        device_list = [x.strip(' ') for x in device_list]

        if device_list == "":
            crt.Dialog.MessageBox("Script Cancelled!")
            return

        # Opens dialog to select command list text file
        command_list = open(crt.Dialog.FileOpenDialog(title="Please select a Command List text file",
                                                    filter="Text Files (*.txt)|*.txt||")).read().splitlines()
        if command_list == "":
            crt.Dialog.MessageBox("Script Cancelled!")
            return

        # Set jump server prompt.  $ for GESA Proxy
        jump_prompt = crt.Dialog.Prompt("What is the base prompt for jump server?:",
                                    "Please enter prompt as shown on Jump Server",
                                    "# or $", False)
        # Capture the user's password
        user_pass = crt.Dialog.Prompt("What is your Tacacs password?:",
                                    "Please enter your Tacacs password",
                                    "password", False)

        for n, elem in enumerate(device_list):
            # Set file name for PRE or POST test. Files are saved to same directory that script is using.

            filename = name_file(test_type, elem)

            # Send return to for NA# that script is waiting for...
            crt.Screen.Send('\r')
            crt.Screen.WaitForString(jump_prompt)

            # Connect to element from device list
            crt.Screen.Send("ssh " + elem + " " + '\r')
            crt.Screen.WaitForString('Password:')
            crt.Screen.Send(user_pass + '\r')
            
            # Wait for connection
            crt.Screen.WaitForString('#')
            crt.Screen.Send('\r')

            # Set prompt for script to expect
            screenrow = crt.Screen.CurrentRow - 1
            prompt_string = crt.Screen.Get(screenrow, 1, screenrow, 40)
            prompt_string = prompt_string.rstrip('\r\n')
            prompt_string = prompt_string.strip()

            crt.Screen.Send('set cli screen-width 255 \r')
            crt.Screen.WaitForString('set cli screen-width 255')

            # Work through command list file - Call command()
            command(filename, command_list, prompt_string)

            # After all commands are parsed the script exits device and for loop continues through device list
            # crt.Sleep(900) <- Leftover Test Piece
            crt.Screen.Send("exit " + '\r')
        if device_types == "2":
            new_device = False
        elif device_types == "1":
            temp_device = crt.Dialog.Prompt("Do you have an additional device type?:\n 1. Yes\n 2. No",
                                     "Please Select Yes or No", "2", False)
            if temp_device == "1":
                new_device = True
            else:
                new_device = False

    if test_type == "2":
        multi_compare(device_list)


def single_device_jump(test_type):
    # Opens dialog to select device list text file
    elem = crt.Dialog.Prompt("What is the name of the device?:", "Enter Device Name", "xx", False)
    elem = elem.rstrip('\r\n')
    # Opens dialog to select command list text file
    command_list = open(crt.Dialog.FileOpenDialog(title="Please select a Command List text file",
                                                  filter="Text Files (*.txt)|*.txt||")).read().splitlines()
    if command_list == "":
        crt.Dialog.MessageBox("Script Cancelled!")
        return
    # Set jump server prompt.  $ for GESA Proxy
    jump_prompt = crt.Dialog.Prompt("What is the base prompt for jump server?:",
                                    "Please enter prompt as shown on Jump Server",
                                    "# or $", False)
    # Set file name for PRE or POST test. Files are saved to same directory that script is using.

    filename = name_file(test_type, elem)

    # Set prompt for script to expect
    prompt_string = (elem + "#")

    # Send return to for NA# that script is waiting for...
    crt.Screen.Send('\r')
    crt.Screen.WaitForString(jump_prompt)

    # Connect to element from device list
    crt.Screen.Send("ssh " + elem + " " + '\r')

    # Wait for connection
    crt.Screen.WaitForString(prompt_string)
    crt.Screen.Send('set cli screen-width 100 \r')
    crt.Screen.WaitForString('set cli screen-width 100')

    # Work through command list file - Call command()
    command(filename, command_list, prompt_string)

    # After all commands are parsed thhe script exits device and for loop continues through device list
    # crt.Sleep(2000) <- Leftover Test Piece
    crt.Screen.Send("exit " + '\r')
    if test_type == "2":
        single_compare(elem)


def single_device(test_type):
    # Opens dialog to select device list text file

    crt.Screen.Send('\r')
    crt.Screen.WaitForString('#')
    crt.Screen.Send('term length 0 \r')
    crt.Screen.WaitForString('#')
    crt.Screen.Send('\r')
    crt.Screen.WaitForString('#')
    screenrow = crt.Screen.CurrentRow - 1
    elem = crt.Screen.Get(screenrow, 1, screenrow, 40)
    elem = elem.replace("#", "")
    elem = elem.rstrip('\r\n')
    elem = elem.strip()

    # Opens dialog to select command list text file
    command_list = open(crt.Dialog.FileOpenDialog(title="Please select a Command List text file",
                                                  filter="Text Files (*.txt)|*.txt||")).read().splitlines()
    if command_list == "":
        crt.Dialog.MessageBox("Script Cancelled!")
        return

    # Set file name for PRE or POST test. Files are saved to same directory that script is using.
    filename = name_file(test_type, elem)

    # Set prompt for script to expect
    prompt_string = (elem + "#")
    # Send return to for NA# that script is waiting for...
    crt.Screen.Send('\r')
    crt.Screen.WaitForString(prompt_string)
    crt.Screen.Send('set cli screen-width 255 \r')
    crt.Screen.WaitForString('set cli screen-width 255')
    # Work through command list file - Call command()
    command(filename, command_list, prompt_string)

    # After all commands are parsed thhe script exits device and for loop continues through device list
    # crt.Sleep(2000) <- Leftover Test Piece
    if test_type == "2":
        single_compare(elem)


def command(filename, command_list, prompt_string):
    # Open output file in append binary mode.  File will be created if it does not exist then appended
    # to with ever command that is run
    for m, cmd in enumerate(command_list):
        fileobj = open(filename, "ab")
        cmd = cmd.strip()
        crt.Screen.Send(cmd + " \r")
        trunc_command = cmd[-10:]
        # crt.Dialog.MessageBox(command)
        crt.Screen.WaitForString('#')
        result = crt.Screen.ReadString(prompt_string)
        fileobj.write(cmd)
        fileobj.write(result)
        fileobj.close()


def multi_compare(device_list):
    compare_request = crt.Dialog.Prompt("Would you like to compare PRE and POST files?:\n 1. Yes\n 2. No",
                                        "Please Make Selection", "1", False)
    pre_list = []
    post_list = []

    # If cancel is pressed there will be no input and script will exit
    if compare_request == "1":
        regex_time_stamp = re.compile('\d{2}:\d{2}:\d{2}|\d{1,2}y\d{1,2}w\d{1,2}d|\d{1,2}w\d{1,2}d|\d{1,2}d\d{1,2}h')
        for n, elem in enumerate(device_list):
            prefilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "PRE_TEST_" + elem + '.txt')
            postfilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "POST_TEST_" + elem + '.txt')
            difffilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "DIFF_" + elem + '.txt')

            with open(prefilename, 'r') as f:
                h = f.readlines()
                for line in h:
                    if regex_time_stamp.search(line) is not None:
                        new_line = re.sub(regex_time_stamp, '', line)
                        pre_list.append(new_line)
                    else:
                        pre_list.append(line)

            with open(postfilename, 'r') as f:
                h = f.readlines()
                for line in h:
                    if regex_time_stamp.search(line) is not None:
                        new_line = re.sub(regex_time_stamp, '', line)
                        post_list.append(new_line)
                    else:
                        post_list.append(line)

            open(difffilename, 'w').close()  # Create the file

            with open(difffilename, 'a') as f:
                diff = difflib.unified_diff(pre_list, post_list, fromfile=prefilename, tofile=postfilename)
                f.writelines(diff)

        crt.Dialog.MessageBox("DIFF COMPLETE!")
    elif compare_request == "2":
        crt.Dialog.MessageBox("No DIFF Requested...SCRIPT COMPLETE!")


def single_compare(elem):
    compare_request = crt.Dialog.Prompt("Would you like to compare PRE and POST files?:\n 1. Yes\n 2. No",
                                        "Please Make Selection", "1", False)
    pre_list = []
    post_list = []

    # If cancel is pressed there will be no input and script will exit
    if compare_request == "1":
        regex_time_stamp = re.compile('\d{2}:\d{2}:\d{2}|\d{1,2}y\d{1,2}w\d{1,2}d|\d{1,2}w\d{1,2}d|\d{1,2}d\d{1,2}h')
        prefilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "PRE_TEST_" + elem + '.txt')
        postfilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "POST_TEST_" + elem + '.txt')
        difffilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "DIFF_" + elem + '.txt')

        with open(prefilename, 'r') as f:
            h = f.readlines()
            for line in h:
                if regex_time_stamp.search(line) is not None:
                    new_line = re.sub(regex_time_stamp, '', line)
                    pre_list.append(new_line)
                else:
                    pre_list.append(line)

        with open(postfilename, 'r') as f:
            h = f.readlines()
            for line in h:
                if regex_time_stamp.search(line) is not None:
                    new_line = re.sub(regex_time_stamp, '', line)
                    post_list.append(new_line)
                else:
                    post_list.append(line)

        open(difffilename, 'w').close()  # Create the file

        with open(difffilename, 'a') as f:
            diff = difflib.unified_diff(pre_list, post_list, fromfile=prefilename, tofile=postfilename)
            f.writelines(diff)
        crt.Dialog.MessageBox("DIFF COMPLETE!")
    elif compare_request == "2":
        crt.Dialog.MessageBox("No DIFF Requested...SCRIPT COMPLETE!")


def name_file(test_type, elem):
    if test_type == "1":
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "PRE_TEST_" + elem + '.txt')
        return filename
    elif test_type == "2":
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "POST_TEST_" + elem + '.txt')
        return filename
    else:
        crt.Dialog.MessageBox("INVALID TEST TYPE!")
        return


main()