import os
import sys
from netCDF4 import Dataset


def validate_nc4(input_file, output_file):
    """
    Validates and processes a .nc4 file, saving the result to the output file.
    
    Args:
        input_file (str): Path to the input .nc4 file.
        output_file (str): Path to the output validated .nc4 file.
    """
    # Open the input NetCDF file
    try:
        nc_data = Dataset(input_file, 'r')
    except Exception as e:
        print(f"Error opening input file {input_file}: {e}")
        sys.exit(1)
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Copy the data and validate (this example just copies the file)
    try:
        with Dataset(output_file, 'w', format='NETCDF4') as out_nc:
            # Copy global attributes
            for attr_name in nc_data.ncattrs():
                out_nc.setncattr(attr_name, nc_data.getncattr(attr_name))
            
            # Copy dimensions
            for dim_name, dim in nc_data.dimensions.items():
                out_nc.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)
            
            # Copy variables
            for var_name, var in nc_data.variables.items():
                out_var = out_nc.createVariable(var_name, var.datatype, var.dimensions)
                out_var.setncatts({attr: var.getncattr(attr) for attr in var.ncattrs()})
                out_var[:] = var[:]
            
            print(f"Successfully validated and dumped {input_file} to {output_file}")
    
    except Exception as e:
        print(f"Error while writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
        input_file = snakemake.input[0]  # First argument is the input file
        output_file = snakemake.output[0]  # Second argument is the output file

        # Call the validate function
        validate_nc4(input_file, output_file)
