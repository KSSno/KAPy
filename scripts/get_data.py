import pandas as pd
import glob

# Path to the TSV file
tsv_file = snakemake.input[0]

# Output file for Snakemake input
output_file = "snakemake_input.txt"

# Read the TSV file using pandas
df = pd.read_csv(tsv_file, sep='\t')

# Initialize a list to store all file paths
all_file_paths = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    file_pattern = row['path']  # 'path' is the column in the TSV
    matching_files = glob.glob(file_pattern, recursive=True)
    all_file_paths.extend(matching_files)

# Write the file paths to the output file
with open(output_file, 'w') as f:
    for file_path in all_file_paths:
        f.write(f"{file_path}\n")
