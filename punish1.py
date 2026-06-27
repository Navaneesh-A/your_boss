import os
import subprocess

def force_back_to_work():
    print("🚨 Threshold crossed! Closing browser and opening VS Code...")
    # Kill the browser (Windows syntax; use 'pkill -f' variants for Mac/Linux)
    os.system("taskkill /F /IM msedge.exe") 
    
    # Open Visual Studio Code
    # Assumes 'code' is added to your system environment variables PATH
    subprocess.Popen(["code", "."], shell=True)
def trigger_tab_kill():
    import os, subprocess
    os.system("taskkill /F /IM msedge.exe")
    subprocess.Popen(["code", "."])


if __name__ == "__main__":
    print("Testing punish1.py independently...")
    force_back_to_work()