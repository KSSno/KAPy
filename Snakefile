import os
import shutil
import pandas as pd
import glob

configfile: "config/testcase_2.yaml"

MMD_OUT_DIR = config['mmd_output']
NC_OUT_DIR = config['nc_output']
INPUT_DIR = config['sample_table']
INPUT_BASE = config['input_base']


df = pd.read_csv(INPUT_DIR, sep='\t')

all_file_paths = []

for index, row in df.iterrows():
    file_pattern = row['path']  # 'path' is the column in the TSV
    matching_files = glob.glob(file_pattern, recursive=True)

    for file_path in matching_files:
        print(file_path)
        struct=os.path.relpath(file_path, INPUT_BASE)
        file_base, _ = os.path.splitext(struct)  # Discard the extension
        all_file_paths.append(file_base)  # Append the file name without extension
    

# Rules
rule all :
    input:
        expand(os.path.join(MMD_OUT_DIR, "{filename}.xml") , filename=all_file_paths),
        expand(os.path.join(NC_OUT_DIR, "{filename}.nc4") , filename=all_file_paths)

rule validate_and_move:
    input:
        f"{INPUT_BASE}{{filename}}.nc4"
    output:
        xml_output = os.path.join(MMD_OUT_DIR, "{filename}.xml"),
        nc_output = os.path.join(NC_OUT_DIR, "{filename}.nc4")
    shell:
        """
        logdir="logs/{wildcards.filename}.txt"
        
        mkdir -p "$(dirname "$logdir")"

        # Get the directory path by removing the last component from the wildcards.filename
        base_dir=$(dirname "{wildcards.filename}")
        nc_dir="{NC_OUT_DIR}/$base_dir"
        mmd_dir="{MMD_OUT_DIR}/$base_dir"
        
        output=$(nc2mmd -i {input} -u "test" -o "$mmd_dir" 2>/dev/null)

        # Check if the output is not empty
        if [[ -n "$output" && "$output" =~ [^[:space:]] ]]; then
            echo "$output" > "$logdir"
        else
            # If no output, copy the input file to the output directory
            cp {input} "$nc_dir"
        fi

        """
