import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from osgeo import gdal
import rasterio
from shapely.geometry import mapping
import xclim.ensembles as xclim_ens

def save_region_ensemble_stats_to_netcdf(config: dict, indicator_id: str, scenario: str, period: str, region: str, inputs: list[str], output: str):
    """
    Saves mean, std and percentiles of indicator for one scenario, period and region as netcdf.

    Args:
        config: configuration from KAPy that contains information from all configuration files
        indicator_id: which parameter in the input file to calculate ensemble statistics for
        scenario: ssp370 for CMIP6 and rcp26 and rcp45 for CMIP5 inputs
        period: near future or far future
        region: id for region in shapefile defined in configuration file to cut out of input file and calculate ensemble statistics for
        inputs: original datasets with 30 year means
    
    Returns:
        Nothing, but saves the ensemble statistics to netcdf for the input scenario, period and region, as well as a spatial plot
    """
    region_datasets = {}
    polygons_file = gpd.read_file(config["region"][region]["shapefile"])
    polygon = gpd.GeoSeries(data=polygons_file.iloc[int(region)].geometry, crs=polygons_file.crs)

    for input_file in inputs:
        dataset = xr.open_dataset(input_file)
        projection = gdal.Open(input_file).GetProjection()
        dataset = dataset.rio.write_crs(projection)
        polygon = polygon.to_crs(projection)
        
        mask = rasterio.features.geometry_mask([mapping(polygon.geometry[0])], out_shape=(len(dataset.Yc), len(dataset.Xc)), transform=dataset.rio.transform(), invert=True)
        mask= xr.DataArray(mask, dims=("Yc", "Xc"))
        clipped_ds = dataset.where(mask, drop=True)
        region_datasets[input_file] = clipped_ds

    datasets = [region_datasets[filename] for filename in region_datasets if period in filename]
    ensemble = xr.combine_nested(datasets, concat_dim="realization")
    dataset_mean_std = xclim_ens.ensemble_mean_std_max_min(ensemble)
    dataset_precentiles = xclim_ens.ensemble_percentiles(ensemble, split=False, values=[float(x) for x in config["ensembles"].values()])
    dataset_total = xr.merge([dataset_mean_std, dataset_precentiles])
    dataset_total.to_netcdf(output)

    plt.figure()
    dataset_total.pr_mean.plot()
    plt.savefig(f"/lustre/storeC-ext/users/klimakverna/development/output/testcase_6/cnrm_hclim/{indicator_id}_{scenario}_{period}_region_{region}_pr_mean.png")