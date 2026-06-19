import subprocess
import sys

def run_script(script_name):
    print(f"Running {script_name}...")
   
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        print(f"Error: {script_name} failed")
        sys.exit(1)


run_script("plotter_weld_neck.py")
run_script("plotter_slip_on.py")
run_script("plotter_blind.py")
run_script("plotter_long_weld_neck.py")
print("Done.")