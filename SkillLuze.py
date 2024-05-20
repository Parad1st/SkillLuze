import json
import os
import sys
import threading

from pynput import keyboard
from termcolor import colored


def on_release(key):
    try:
        if key == keyboard.Key.f1:
            Aimbot.update_status_aimbot()
        if key == keyboard.Key.f2:
            Aimbot.clean_up()
    except NameError:
        pass

def main():
    global SkillLuze
    SkillLuze = Aimbot(collect_data = "collect_data" in sys.argv)
    SkillLuze.start()

def setup():
    path = "lib/config"
    if not os.path.exists(path):
        os.makedirs(path)

    print("[SETUP] Let's start setting up...")
    def prompt(str):
        valid_input = False
        while not valid_input:
            try:
                number = float(input(str))
                valid_input = True
            except ValueError:
                print("[ERROR] Error! Enter numbers only (for example: 5.2)")
        return number

    xy_sens = prompt("X and Y sensitivity from game settings: ")
    targeting_sens = prompt("Sensitivity when aiming from game settings: ")

    print("[SETUP] SiillLuze")
    sensitivity_settings = {"xy_sens": xy_sens, "targeting_sens": targeting_sens, "xy_scale": 10/xy_sens, "targeting_scale": 1000/(targeting_sens * xy_sens)}

    with open('lib/config/config.json', 'w') as outfile:
        json.dump(sensitivity_settings, outfile)
    print("[!] Sensitivity is set")
    print("[!] If you want to configure the sensor differently, delete the config file along the path lib/config/config.json")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    print(colored('''
    
    ░██████╗██╗░░██╗██╗██╗░░░░░██╗░░░░░██╗░░░░░██╗░░░██╗███████╗███████╗
    ██╔════╝██║░██╔╝██║██║░░░░░██║░░░░░██║░░░░░██║░░░██║╚════██║██╔════╝
    ╚█████╗░█████═╝░██║██║░░░░░██║░░░░░██║░░░░░██║░░░██║░░███╔═╝█████╗░░
    ░╚═══██╗██╔═██╗░██║██║░░░░░██║░░░░░██║░░░░░██║░░░██║██╔══╝░░██╔══╝░░
    ██████╔╝██║░╚██╗██║███████╗███████╗███████╗╚██████╔╝███████╗███████╗
    ╚═════╝░╚═╝░░╚═╝╚═╝╚══════╝╚══════╝╚══════╝░╚═════╝░╚══════╝╚══════╝

    (By Parad1st)''', "yellow"))
    print(colored('''Attention! This neural network is free and distributed on GitHub: https://github.com/Parad1st/SkillLuze''', "red"))

    path_exists = os.path.exists("lib/config/config.json")
    if not path_exists or ("setup" in sys.argv):
        if not path_exists:
            print("[ERROR] sensitivity is not set")
        setup()
    path_exists = os.path.exists("lib/data")
    if "collect_data" in sys.argv and not path_exists:
        os.makedirs("lib/data")
    from lib.aimbot import Aimbot
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    main()
