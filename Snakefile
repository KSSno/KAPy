import os
import shutil
import pandas as pd
import glob

configfile: "config/testcase_2.yaml"
# Input and output directories
# INPUT_DIR = "/home/shamlym/workspace/klima-kverna/nc/"
OUTPUT_DIR = "results"
INPUT_DIR = config['sample_table']
input_base = "/home/shamlym/workspace/klima-kverna/nc/"
# Create output directory if it doesn't exist
# if not os.path.exists(OUTPUT_DIR):
#     os.makedirs(OUTPUT_DIR)

# # Get a list of .nc files from the input directory
# nc_files = [f.split(".")[0] for f in os.listdir(INPUT_DIR) if f.endswith(".nc4")]

df = pd.read_csv(INPUT_DIR, sep='\t')

# Initialize a list to store all file paths
all_file_paths = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    file_pattern = row['path']  # 'path' is the column in the TSV
    matching_files = glob.glob(file_pattern, recursive=True)

    for file_path in matching_files:
        print(file_path)
        struct=os.path.relpath(file_path, input_base)
        # struct = os.path.dirname(file_path).replace(input_base , "")
        # subdir, filename = os.path.split(struct)         # Split into subdir and file

        file_base, _ = os.path.splitext(struct)  # Discard the extension
        all_file_paths.append(file_base)  # Append the file name without extension
    

print(all_file_paths)
# Rules
rule all :
    input:
        expand(os.path.join(OUTPUT_DIR, "{filename}.xml") , filename=all_file_paths),
        expand(os.path.join(OUTPUT_DIR, "{filename}.nc4") , filename=all_file_paths)

rule validate_and_move:
    input:
        f"{input_base}{{filename}}.nc4"
    output:
        xml_output = os.path.join(OUTPUT_DIR, "{filename}.xml"),
        nc_output = os.path.join(OUTPUT_DIR, "{filename}.nc4")
    shell:
        """
         logdir="logs/{wildcards.filename}.txt"
        
        # Create the log directory if it does not exist
        mkdir -p "$(dirname "$logdir")"

        output=$(nc2mmd -i {input} -u "test" -o {OUTPUT_DIR} 2>/dev/null)

        # Check if the output is not empty
        if [[ -n "$output" && "$output" =~ [^[:space:]] ]]; then
            echo "$output" > "$logdir"
        else
            # If no output, copy the input file to the output directory
            cp {input} {OUTPUT_DIR}
        fi

        """
