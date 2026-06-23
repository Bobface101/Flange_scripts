import subprocess
import sys

def run_script(script_name):
    print(f"Running {script_name}...")
   
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        print(f"Error: {script_name} failed")
        sys.exit(1)


run_script("PLOTTER_Mod_B_Type_01.py")
run_script("PLOTTER_Mod_E_Type_01.py")
run_script("PLOTTER_Mod_F_Type_01.py")
run_script("PLOTTER_Mod_B_Type_11.py")
run_script("PLOTTER_Mod_E_Type_11.py")
run_script("PLOTTER_Mod_F_Type_11.py")
print("Done.")