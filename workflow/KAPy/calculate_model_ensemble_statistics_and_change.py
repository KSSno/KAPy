import csv
from pathlib import Path
from typing import Literal
import matplotlib.pyplot as plt
from glob import glob
import xarray as xr
from xclim import ensembles as xe
import yaml

from KAPy.save_change_to_netcdf import save_change_to_netcdf
from KAPy.plots import makeBoxplot


def calculate_ensemble_mean(
    output_path: str,
    indicator_id: str,
    scenario: str,
    ensemble_filename: str,
    config: dict,
    CMIP_version: None | int = None,
    region_id: str | None = None
):    
    if "hist" not in scenario:
        if not region_id:
            # testcase 1
            periods = [2, 3]
            search_dir = f"{output_path}/KAPy_results/7.netcdf"
            netcdf_files = glob(f"{search_dir}/**/{indicator_id}_{scenario}*.nc", recursive=True)
        else:
            # testcase 6
            periods = [1, 2]
            search_dir = f"{output_path}/model_results"
            netcdf_files = glob(f"{search_dir}/**/{indicator_id}_{scenario}_??_region_{region_id}.nc", recursive=True)
    else:
        # testcase 1
        periods = [1, 2, 3]
        search_dir = f"{output_path}/KAPy_results/4.ensstats"

        match CMIP_version:
            case 6:
                netcdf_files = glob(f"{search_dir}/**/{indicator_id}_CMIP6_{scenario}*.nc", recursive=True)
            case 5:
                netcdf_files = glob(f"{search_dir}/**/{indicator_id}_CMIP5_{scenario}*.nc", recursive=True)
            case _:
                print("Invalid CMIP version")
                return

    ensemble_ds = xr.open_mfdataset(netcdf_files, concat_dim="realization", combine="nested")

    try:
        ensemble_ds = ensemble_ds.drop_vars(
            [
                "indicator_stdev",
                "indicator_min",
                "indicator_max",
                "indicator",
                "indicator_mean_change",
                "indicator_mean_relative_change",
            ]
        )
    except ValueError:
        try:
            ensemble_ds = ensemble_ds.drop_vars(
                [
                    "indicator_stdev",
                    "indicator_min",
                    "indicator_max",
                    "indicator",
                ]
            )
        except ValueError:
            # No variables need to be dropped
            pass

    ensemble_ds = ensemble_ds.rename_vars({"indicator_mean": "indicator"})
    ensemble_ds_stats = xe.ensemble_mean_std_max_min(ensemble_ds)
    ensemble_ds_percentiles = xe.ensemble_percentiles(
        ensemble_ds, split=False, values=[float(x) for x in config["ensembles"].values()]
    )

    ensemble_ds_result = xr.merge([ensemble_ds_stats, ensemble_ds_percentiles])
    ensemble_ds_result = ensemble_ds_result.assign(periodID=periods)
    ensemble_ds_result.to_netcdf(ensemble_filename)


def plot_and_save_spatial_plot(ensemble_change_filename: str, figure_filename: str):
    cmap = plt.cm.PuOr
    alpha = 0.8
    plot_limits = [-20, 20]
    ensemble_change_ds = xr.open_dataset(ensemble_change_filename)

    for period in [2, 3]:
        plt.figure()
        ensemble_change_ds["indicator_mean_relative_change"].sel(periodID=period).plot(
            robust=True, vmin=plot_limits[0], vmax=plot_limits[-1], cmap=cmap, alpha=alpha
        )
        plt.savefig(f"{figure_filename}_period_{period}.png")


def create_config(
    path_to_config: str,
    path_to_periods: str,
    testcase_no: int,
    scenario: str,
    indicator_id: str,
    units: str,
    indicator_name: str,
    region_id: str | None = None
) -> tuple[dict[str, dict[str, str]], list[str], Literal[5, 6] | None, bool]:
    historical_period = False
    config = {}
    config["scenarios"] = {}
    config["periods"] = {}
    if region_id:
        config["region"] = region_id
        n_col_period = 5
    else:
        config["region"] = None
        n_col_period = 4
    
    with open(path_to_config) as f:
        config["ensembles"] = yaml.safe_load(f)[f"testcase_{testcase_no}"]["ensembles"]

    with open(path_to_periods) as f:
        periods_config = csv.reader(f, delimiter="\t")
        for line_no, line in enumerate(periods_config):
            if line_no == 0:
                keys = line
                continue

            if "#" in line[0]:
                continue

            config["periods"][f"{line_no}"] = {keys[idx]: line[idx] for idx in range(0, n_col_period)}
            
            if line[1] == "Histrorical":
                historical_period = True

    config["indicators"] = {indicator_id: {"units": units, "name": indicator_name}}
   
    if historical_period:
        config["scenarios"] = {
            "historical": {
                "id": "historical",
                "description": "Historical values",
                "scenarioStrings": ["_hist_"],
                "hexcolour": "66C2A5",
            }
        }

    CMIP5_scenarios = ["rcp26", "rcp45"]
    CMIP6_scenarios = ["ssp370"]
    scenarios = []
    if scenario == "all":
        CMIP_version = None
        scenarios = CMIP5_scenarios + CMIP6_scenarios
        config["scenarios"]["rcp26"] = {
            "id": "rcp26",
            "description": "Low emissions scenario (RCP2.6)",
            "scenarioStrings": ["_rcp26_"],
            "hexcolour": "FC8D62",
        }
        config["scenarios"]["rcp45"] = {
            "id": "rcp45",
            "description": "Medium emissions scenario (RCP4.5)",
            "scenarioStrings": ["_rcp45_"],
            "hexcolour": "8DA0CB",
        }
        config["scenarios"]["ssp370"] = {
            "id": "ssp370",
            "description": "2nd worst scenario (SSP370)",
            "scenarioStrings": ["_ssp370_"],
            "hexcolour": "66C2A5",
        }
    elif scenario in CMIP5_scenarios:
        CMIP_version = 5
        scenarios = CMIP5_scenarios
        config["scenarios"]["rcp26"] = {
            "id": "rcp26",
            "description": "Low emissions scenario (RCP2.6)",
            "scenarioStrings": ["_rcp26_"],
            "hexcolour": "FC8D62",
        }
        config["scenarios"]["rcp45"] = {
            "id": "rcp45",
            "description": "Medium emissions scenario (RCP4.5)",
            "scenarioStrings": ["_rcp45_"],
            "hexcolour": "8DA0CB",
        }
    elif scenario in CMIP6_scenarios:
        CMIP_version = 6
        scenarios = CMIP6_scenarios
        config["scenarios"]["ssp370"] = {
            "id": "ssp370",
            "description": "2nd worst scenario (SSP370)",
            "scenarioStrings": ["_ssp370_"],
            "hexcolour": "FC8D62",
        }
    else:
        CMIP_version = None

    return config, scenarios, CMIP_version, historical_period


def create_csv(netcdf_statistics_filename: str, csv_filename: str):
    ds = xr.open_dataset(netcdf_statistics_filename)
    df_indicator_mean = ds.indicator.mean(dim=["Yc", "Xc"]).to_dataframe()
    df_indicator_mean.to_csv(csv_filename)


if __name__ == "__main__":
    scenarios = ["rcp26", "ssp370", "all"]
    CMIP_scenarios = {"CMIP5": ["rcp26", "rcp45"], "CMIP6": ["ssp370"]}
    indicator_id = "102"
    units = "kg m-2 s-1"
    indicator_name = "Annual mean precipitation by period"

    # testcase 1
    # calculate_change = True
    # testcase_no = 1
    # region_id = None

    # testcase 6
    calculate_change = False
    testcase_no = 6
    region_id = "7"

    base_path = "/lustre/storeC-ext/users/klimakverna/development"
    output_base_path = f"{base_path}/output/testcase_{testcase_no}/model_ensembles"
    path_to_config = f"{base_path}/Klimakverna-Pilot1/config/config.yaml"
    path_to_periods = f"{base_path}/Klimakverna-Pilot1/config/testcase_{testcase_no}/periods.tsv"
    
    for scenario in scenarios:
        # Create config for this scenario/CMIP version, periods and indicator
        config, scenarios, CMIP_version, historical_period = create_config(path_to_config, path_to_periods, testcase_no, scenario, indicator_id, units, indicator_name, region_id)
        path_to_save_netcdf = f"{output_base_path}/CMIP{CMIP_version}"
        
        if scenario != "all":
            # Note on csv filenames:
            # scenario has to be the third word, since makeBoxplot uses the third word in the filename
            # for mapping the scenarios in the legend
            if region_id:
                statistics_filenames = [f"{path_to_save_netcdf}/{scenario}/{indicator_id}_{scenario}_ensemble_statistics_region_{region_id}.nc" for scenario in scenarios]
                statistics_csv_filenames = [f"{path_to_save_netcdf}/{scenario}/{indicator_id}_ensemble_{scenario}_statistics_region_{region_id}.csv" for scenario in scenarios]
            else:
                statistics_filenames = [f"{path_to_save_netcdf}/{scenario}/{indicator_id}_{scenario}_ensemble_statistics.nc" for scenario in scenarios]
                statistics_csv_filenames = [f"{path_to_save_netcdf}/{scenario}/{indicator_id}_ensemble_{scenario}_statistics.csv" for scenario in scenarios]

            if calculate_change:
                change_filenames = [f"{path_to_save_netcdf}/{scenario}/{indicator_id}_{scenario}_ensemble_change.nc" for scenario in scenarios]
           
            if historical_period:
                historical_filename = f"{path_to_save_netcdf}/{indicator_id}_CMIP{CMIP_version}_historical_statistics.nc"
                historical_csv_filename = f"{path_to_save_netcdf}/{indicator_id}_CMIP{CMIP_version}_historical_statistics.csv"

            # Calculate ensemble statistics over models and save to netcdf
            output_path = f"{base_path}/output/testcase_{testcase_no}"
            if historical_period:
                if not Path(historical_filename).exists():
                    calculate_ensemble_mean(output_path, indicator_id, "historical", historical_filename, config, CMIP_version=CMIP_version)

            for scenario, ensemble_statistics in zip(scenarios, statistics_filenames):
                if not Path(ensemble_statistics).exists():
                    calculate_ensemble_mean(output_path, indicator_id, scenario, ensemble_statistics, config, region_id=region_id)

            # Calculate ensemble change over models and save to netcdf
            if calculate_change:
                for scenario, ensemble_change, ensemble_statistics in zip(scenarios, change_filenames, statistics_filenames):
                    if not Path(ensemble_change).exists():
                        ensemble_stats_files = [str(ensemble_statistics), str(historical_filename)]
                        netcdf_filename = [str(ensemble_change)]
                        save_change_to_netcdf(config, indicator_id, scenario, ensemble_stats_files, netcdf_filename)

                    # Plot spatial plot from ensemble change netcdf
                    plot_and_save_spatial_plot(
                        str(ensemble_change),
                        f"{path_to_save_netcdf}/{scenario}/{indicator_id}_{scenario}_ensemble_mean_relative_change",
                    )

            # Plot box plot from ensemble statistics netcdf
            csv_files_for_boxplot = [filename for filename in statistics_csv_filenames]
            if historical_period:
                csv_files_for_boxplot.append(historical_csv_filename)
                create_csv(historical_filename, historical_csv_filename)
            
            for scenario, ensemble_statistics, ensemble_csv in zip(scenarios, statistics_filenames, statistics_csv_filenames):
                ds_scenario = xr.open_dataset(ensemble_statistics)
                if region_id:
                    ds_scenario.indicator.to_dataframe().to_csv(ensemble_csv)
                else:
                    ds_to_csv = ds_scenario.indicator.mean(dim=["Yc", "Xc"])
                    ds_to_csv = ds_to_csv.to_dataframe()
                    ds_to_csv.to_csv(ensemble_csv)
            
            if region_id:
                plot_name = f"{path_to_save_netcdf}/{indicator_id}_CMIP{CMIP_version}_ensemble_boxplot_region_{region_id}.png"
            else:
                plot_name = f"{path_to_save_netcdf}/{indicator_id}_CMIP{CMIP_version}_ensemble_boxplot.png"
            
            makeBoxplot(
                config,
                indicator_id,
                csv_files_for_boxplot,
                [plot_name],
            )
        else:
            # Antar at csvene exsisterer
            if region_id:
                plot_name = f"{output_base_path}/{indicator_id}_ensemble_boxplot_region_{region_id}.png"
                
                csv_files_for_boxplot = []
                nc_files_for_csv = []
                for CMIP_version, scenarios in CMIP_scenarios.items():
                    filename_nc = [f"{output_base_path}/{CMIP_version}/{scenario}/{indicator_id}_{scenario}_ensemble_statistics_region_{region_id}.nc" for scenario in scenarios]
                    nc_files_for_csv.extend(filename_nc)
                    filename_csv = [f"{output_base_path}/{CMIP_version}/{scenario}/{indicator_id}_ensemble_{scenario}_statistics_region_{region_id}.csv" for scenario in scenarios]
                    csv_files_for_boxplot.extend(filename_csv)

                # Combine sceanrios in one output csv with columns 
                datasets = [xr.open_dataset(filename) for filename in nc_files_for_csv]
                scenarios = [scenario for scenario in CMIP_scenarios.values() for scenario in scenario]
                ds_csv = xr.Dataset()
                variable_names = ["upper_percentile", "middle_percentile", "lower_percentile"]
                for percentile, name in zip(datasets[0].percentiles, variable_names):
                    data= [
                        datasets[0].indicator.sel(percentiles=percentile).data, 
                        datasets[1].indicator.sel(percentiles=percentile).data, 
                        datasets[2].indicator.sel(percentiles=percentile).data
                        ]

                    da = xr.DataArray(data,
                                    dims=["scenario", "period"],
                                    coords={
                                        "scenario": scenarios,
                                        "period": ["nf", "ff"],
                                        "region": region_id
                                    })


                    ds_csv  = ds_csv.assign(**{name: da})

                ds_csv.to_dataframe(dim_order=["scenario", "period"]).to_csv(f"{output_base_path}/ensemble_statistics_scenarios_region_{region_id}.csv")
            else:
                plot_name = f"{output_base_path}/{indicator_id}_ensemble_boxplot.png"
                csv_files_for_boxplot = []
                for CMIP_version, scenarios in CMIP_scenarios.items():
                    filename_csv = [f"{output_base_path}/{CMIP_version}/{scenario}/{indicator_id}_ensemble_{scenario}_statistics.csv" for scenario in scenarios]
                    csv_files_for_boxplot.extend(filename_csv)

            makeBoxplot(
                config,
                indicator_id,
                csv_files_for_boxplot,
                [plot_name],
            )
        
