#!/usr/bin/env python
# coding: utf-8

import sys
import importlib.util
import pandas as pd
import numpy as np
from pathlib import Path

if len(sys.argv) != 2:
	raise SystemExit(
        'A project should be specified: generate_neighbourhood_properties.py <PROJECT>'
    )

project = sys.argv[1]
# When exporting to .py file, remove "" from "__file__"
main_path = Path(__file__).resolve().parents[3]  # data_processing folder
spec = importlib.util.spec_from_file_location(f'..{project}', f'scripts/config_files/{project}.py')
project_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_config)

#========================== Neighbourhood list ==================================

print('\nLoading complete list of neighbourhoods\n')
neighbourhood_list_file = main_path / "input_data" / project / "neighbourhood_list.csv"
df_neighbourhood_list = pd.read_csv(neighbourhood_list_file, dtype={"neighbourhood_code": object})

number_of_objects_total = len(df_neighbourhood_list)
print("Found ", number_of_objects_total, " neighbourhoods in total")

# removing redundant columns
df_neighbourhood_list = df_neighbourhood_list[['neighbourhood_code']]
df_neighbourhood_list.set_index('neighbourhood_code', inplace=True)

#======================== Neighbourhood properties =========================================

print('\nLoading other neighbourhood properties\n')
properties_file = main_path / "input_data" / project / 'neighbourhood_heat_demand.csv'
neighbourhood_properties = pd.read_csv(properties_file, index_col=0).astype(np.float64)

number_of_properties_objects = len(neighbourhood_properties)
print("Found ", number_of_properties_objects, " neighbourhoods with additional properties")

if number_of_properties_objects != number_of_objects_total:
	print(
        'WARNING: number of objects with additional properties is not equal to total number of',
        'objects!'
    )

## Do stuff with the columns
utility_scaling = project_config.KEY_FIGURES['m2_utility_to_house_equivalents']

# space_heating_demand_per_m2_utility = demand_weq_rv * utility_scaling
neighbourhood_properties["space_heating_demand_per_m2_utility"] = (
	neighbourhood_properties['Vraag_perWEQ_RV [ giga J per WEQ*yr]'] * utility_scaling
)
# space_heating_demand_per_house = demand_weq_rv
neighbourhood_properties.rename(
    columns = {'Vraag_perWEQ_RV [ giga J per WEQ*yr]': 'space_heating_demand_per_house'},
    inplace = True
)

# hot_water_demand_per_m2_utility = demand_weq_tw * utility_scaling
neighbourhood_properties["hot_water_demand_per_m2_utility"] = (
    neighbourhood_properties['Vraag_perWEQ_TW [ giga J per WEQ*yr]'] * utility_scaling
)

# hot_water_demand_per_house = demand_weq_tw
neighbourhood_properties.rename(
    columns = {'Vraag_perWEQ_TW [ giga J per WEQ*yr]': 'hot_water_demand_per_house'},
    inplace = True
)

# electricity_demand_per_house = demand_weq_k + demand_weq_app + demand_weq_vent
neighbourhood_properties["electricity_demand_per_house"] = (
    neighbourhood_properties['Vraag_perWEQ_K [ giga J per WEQ*yr]'] +
    neighbourhood_properties['Vraag_perWEQ_App [ giga J per WEQ*yr]'] +
    neighbourhood_properties['Vraag_perWEQ_Vent [ giga J per WEQ*yr]']
)

# electricity_demand_per_m2_utility = (demand_weq_k + demand_weq_app + demand_weq_vent) *
# utility_scaling
neighbourhood_properties["electricity_demand_per_m2_utility"] = (
    (neighbourhood_properties["electricity_demand_per_house"] +
    neighbourhood_properties['Vraag_perWEQ_Vent [ giga J per WEQ*yr]']) *
    utility_scaling
)

## Adding additional (empty) columns
neighbourhood_properties['share_of_houses_demolished'] = 0
neighbourhood_properties['number_of_new_apartments'] = 0
neighbourhood_properties['number_of_new_terraced_houses'] = 0
neighbourhood_properties['number_of_new_detached_houses'] = 0
neighbourhood_properties['number_of_new_semi_detached_houses'] = 0
neighbourhood_properties['number_of_new_houses_unknown_type'] = 0
neighbourhood_properties['epi_of_new_houses'] = 0.9
neighbourhood_properties['size_of_new_houses'] = 100.0

## Drop unused columns
neighbourhood_properties.drop(
    ['Vraag_perWEQ_K [ giga J per WEQ*yr]', 'Vraag_perWEQ_App [ giga J per WEQ*yr]'],
    axis=1,
    inplace=True
)

# Merging the dataframes (why?)
df_neighbourhoods = df_neighbourhood_list.merge(
    neighbourhood_properties,
    how='left',
    on='neighbourhood_code'
)

#========================= Neighbourhood percentage of heat network =======================

print('\nLoading data on heat network percentages\n')
heat_network_file = main_path / "input_data" / project / "existing_heat_network_share.csv"
df_heat_network_percentage = pd.read_csv(heat_network_file, index_col=0, squeeze=True)

number_of_objects_with_heat_network = len(df_heat_network_percentage)
print("Found ", number_of_objects_with_heat_network, " neighbourhoods with a percentage defined.\n")

# Create column of percentage of heat networks for all neighbourhoods
df_neighbourhoods = df_neighbourhoods.merge(
    df_heat_network_percentage,
    how='left',
    on='neighbourhood_code'
)

# Add zero's to neighbourhoods that don't occur in df_heat_network_percentage
df_neighbourhoods = df_neighbourhoods.fillna(0)

# export to CSV
print('Exporting results to CSV\n')
output_file = main_path / "input_data" / project / "neighbourhood_properties.csv"
df_neighbourhoods.to_csv(output_file)
print('Success! Results can be found in {}'.format(output_file))
