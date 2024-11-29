import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import xarray as xr

# ds = edata.from_source("file", "/lustre/storeC-ext/users/klimakverna/development/kaja/data/shapefile")
ds = gpd.read_file("/lustre/storeC-ext/users/klimakverna/development/kaja/data/shapefile")
print(ds)
print(type(ds))

# ds = xr.open_dataset("/lustre/storeB/project/KSS/kin2100_2024/Indices/30yr-diff-files_for_plotting/pr/30yrmean_nf-change_cnrm-r1i1p1f2-hclim_ssp370_3dbc-eqm-sn2018v2005_rawbc_norway_1km_pr_annual_merged.nc")

plt.figure()
ds.plot()
plt.savefig("/lustre/storeC-ext/users/klimakverna/development/kaja/KAPy/test_geometry.png")
print(ds.iloc[5].geometry)
print(type(ds.iloc[5].geometry))
region5 = gpd.GeoSeries(data=ds.iloc[5].geometry, crs = "EPSG:32633")
plt.figure()
gpd.GeoSeries.plot(region5)
plt.savefig("/lustre/storeC-ext/users/klimakverna/development/kaja/KAPy/test_geometry_part.png")

# clipping
region7 = gpd.GeoSeries(data=ds.iloc[7].geometry, crs = ds.crs)
region_all_minus_7 = gpd.GeoSeries(data=pd.concat([ds.iloc[:7].geometry, ds.iloc[8:].geometry]), crs = ds.crs)
clipped = ds.clip(mask=region_all_minus_7, keep_geom_type=True)
print(type(clipped))
plt.figure()
clipped.plot()
plt.savefig("/lustre/storeC-ext/users/klimakverna/development/kaja/KAPy/test_geometry_clip.png")


plt.figure()
gpd.GeoSeries.plot(region7)
plt.savefig("/lustre/storeC-ext/users/klimakverna/development/kaja/KAPy/test_geometry_region7.png")

ds = xr.Dataset.from_dataframe(ds)
print(ds)
print(ds.geometry.sel(index=5).data)