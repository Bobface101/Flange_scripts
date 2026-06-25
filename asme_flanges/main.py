import subprocess
import sys
import os 

def run_script(script_name):
    print(f"Running {script_name}...")
   

    script_dir = os.path.dirname(os.path.abspath(__file__))
    

    script_path = os.path.join(script_dir, script_name)
    
    result = subprocess.run([sys.executable, script_path])
    
    if result.returncode != 0:
        print(f"Error: {script_name} failed")
        sys.exit(1)

run_script("open_output.py")

run_script("plotter_blind.py")

run_script("plotter_weld_neck.py")
run_script("plotter_slip_on.py")
run_script("plotter_long_weld_neck.py")

print("Done.")