import os 
import codecs # Import codecs for the BOM

script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, 'commands.scr')

# Create the file and write the UTF-16 LE BOM exactly once
with open(output_file, 'wb') as f:
    f.write(codecs.BOM_UTF16_LE)