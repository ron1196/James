#!/usr/bin/python3.6

import sys
import os
import subprocess
import argparse

#Launcher for James

def parse_cli_args():
    parser = argparse.ArgumentParser(description="James Launcher - Pokemon Go Bot for Discord")
    parser.add_argument("--start","-s",help="Starts James",action="store_true")
    parser.add_argument("--auto-restart","-r",help="Auto-Restarts James in case of a crash.",action="store_true")
    parser.add_argument("--debug","-d",help="Prevents output being sent to Discord DM, as restarting could occur often.",action="store_true")
    return parser.parse_args()

def run_James(autorestart):
    interpreter = sys.executable
    if interpreter is None:
        raise RuntimeError("Python could not be found")

    cmd = [interpreter, "james", "launcher"]

    while True:
        if args.debug:
            cmd.append("debug")
        try:
            code = subprocess.call(cmd)
        except KeyboardInterrupt:
            code = 0
            break
        else:
            if code == 0:
                break
            elif code == 26:
                #standard restart
                print("")
                print("Restarting James")
                print("")
                continue
            else:
                if not autorestart:
                    break
                print("")
                print("Restarting James from crash")
                print("")

    print("James has closed. Exit code: {exit_code}".format(exit_code=code))

args = parse_cli_args()

if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)

    if args.start:
        print("Launching James...")
        run_James(autorestart=args.auto_restart)
