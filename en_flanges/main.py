import subprocess
import sys

def run_script(script_name):
    print(f"Running {script_name}...")
   
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        print(f"Error: {script_name} failed")
        sys.exit(1)


run_script("plotter_blind_flat.py")
run_script("plotter_blind_rf.py")
run_script("plotter_blind_male.py")
run_script("plotter_blind_female.py")
print("Done.")