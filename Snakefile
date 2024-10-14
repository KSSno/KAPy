import os
import shutil

# Input and output directories
INPUT_DIR = "/home/shamlym/workspace/klima-kverna/nc/valid_nc/"
OUTPUT_DIR = "/home/shamlym/workspace/klima-kverna/nc/valid_nc/valid/"

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Get a list of .nc files from the input directory
nc_files = [f.split(".")[0] for f in os.listdir(INPUT_DIR) if f.endswith(".nc")]

# Rules
rule all :
    input:
        expand(os.path.join(OUTPUT_DIR, "{filename}.xml"), filename=nc_files)

rule validate_and_move:
    input:
        os.path.join(INPUT_DIR, "{filename}.nc")
    output:
        os.path.join(OUTPUT_DIR, "{filename}.xml")
    shell:
        """
        nc2mmd -i {input} -u "test" -o {OUTPUT_DIR}
        """
