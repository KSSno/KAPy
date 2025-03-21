import xarray as xr
import numpy as np

def timeseries_netcdf_to_csv(config: dict, indicator_id: str, region: str, inputs: list[str], output: str):
    indicator_name = config["indicators"][indicator_id]["variables"]
    datasets = {}
    dataarrays = []
    
    for input_file in inputs:
        ds = xr.open_dataset(input_file)
        scenario = ds.scenario.values[0]

        if scenario in datasets:
            datasets[scenario]["ds"].append(ds)
            datasets[scenario]["time"] = np.sort(np.unique(np.concatenate([datasets[scenario]["time"], ds.time.values])))
        else:
            datasets[scenario] = {}
            datasets[scenario]["ds"] = [ds]
            datasets[scenario]["time"] = ds.time.values

    all_time_values = [datasets[scenario]["time"] for scenario in datasets] 
    all_time_values = np.concatenate(all_time_values)

    for scenario, scenario_data in datasets.items():
        data = np.full(len(all_time_values), np.nan)

        for ds in scenario_data["ds"]:
            ds_time = ds.time.values
        
            for idx, time_value in enumerate(ds_time):
                index = np.where(all_time_values == time_value)[0]
                if index.size > 0:
                    data[index[0]] = ds[indicator_name].values[idx]

        dataarrays.append(xr.DataArray(data, dims=["time"], coords={"time": all_time_values}, name=scenario))

    ds_csv = xr.merge(dataarrays, compat="no_conflicts")
    ds_csv.to_dataframe().to_csv(output)
