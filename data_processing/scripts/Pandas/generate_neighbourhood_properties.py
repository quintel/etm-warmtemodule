#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from pathlib import Path

# When exporting to .py file, remove "" from "__file__"
main_path = Path(__file__).resolve().parents[3]  # data_processing folder

#========================== Neighbourhood list ==================================

print('\nLoading complete list of neighbourhoods\n')
neighbourhood_list_file = main_path / "input_data" / "buurten_OB2021.csv"
df_neighbourhood_list = pd.read_csv(Path(neighbourhood_list_file), dtype={"BU_CODE": object})

number_of_objects_total = len(df_neighbourhood_list)
print("Found ", number_of_objects_total, " neighbourhoods in total")

# removing redundant columns
print('Removing redundant columns')
keep = ['BU_CODE']
df_neighbourhood_list = df_neighbourhood_list[keep]
df_neighbourhood_list.set_index('BU_CODE', inplace=True)
df_neighbourhood_list.index.names = ['neighbourhood_code']

#======================== Neighbourhood properties =========================================

print('\nLoading other neighbourhood properties\n')
neighbourhood_properties_file = main_path / "input_data" / "Warmtevraag en WEQ data SA.csv"
df_neighbourhood_properties = pd.read_csv(Path(neighbourhood_properties_file), dtype=object)
df_neighbourhood_properties.set_index('BU_CODE', inplace=True)
df_neighbourhood_properties.index.names = ['neighbourhood_code']

print('Removing redundant columns')
keep = [
'InStudieGebied?',
'Vraag_perWEQ_RV [ giga J per WEQ*yr]',
'Vraag_perWEQ_TW [ giga J per WEQ*yr]',
'Vraag_perWEQ_K [ giga J per WEQ*yr]',
'Vraag_perWEQ_App [ giga J per WEQ*yr]'
]

df_neighbourhood_properties = df_neighbourhood_properties[keep]

# Select only rows for neighbourhoods in our region of interest
df_neighbourhood_properties = df_neighbourhood_properties[df_neighbourhood_properties['InStudieGebied?'] == "1"]

number_of_properties_objects = len(df_neighbourhood_properties)
print("Found ", number_of_properties_objects, " neighbourhoods with additional properties")

if number_of_properties_objects != number_of_objects_total:
	print("WARNING: number of objects with additional properties is not equal to total number of objects!")

## Do stuff with the columns

# space_heating_demand_per_m2_utility = Vraag_perWEQ_RV [ giga J per WEQ*yr] / 130
df_neighbourhood_properties["space_heating_demand_per_m2_utility"] = df_neighbourhood_properties['Vraag_perWEQ_RV [ giga J per WEQ*yr]'].apply(pd.to_numeric) / 130.0

# space_heating_demand_per_house = Vraag_perWEQ_RV [ giga J per WEQ*yr]
df_neighbourhood_properties.rename(columns = {'Vraag_perWEQ_RV [ giga J per WEQ*yr]': 'space_heating_demand_per_house'}, inplace = True)

# hot_water_demand_per_m2_utility = Vraag_perWEQ_TW [ giga J per WEQ*yr] / 130
df_neighbourhood_properties["hot_water_demand_per_m2_utility"] = df_neighbourhood_properties['Vraag_perWEQ_TW [ giga J per WEQ*yr]'].apply(pd.to_numeric) / 130.0

# hot_water_demand_per_house = Vraag_perWEQ_TW [ giga J per WEQ*yr]
df_neighbourhood_properties.rename(columns = {'Vraag_perWEQ_TW [ giga J per WEQ*yr]': 'hot_water_demand_per_house'}, inplace = True)

# electricity_demand_per_house = Vraag_perWEQ_K [ giga J per WEQ*yr] + Vraag_perWEQ_App [ giga J per WEQ*yr]
df_neighbourhood_properties["electricity_demand_per_house"] = df_neighbourhood_properties['Vraag_perWEQ_K [ giga J per WEQ*yr]'].apply(pd.to_numeric) + df_neighbourhood_properties['Vraag_perWEQ_App [ giga J per WEQ*yr]'].apply(pd.to_numeric) 

# electricity_demand_per_m2_utility = (Vraag_perWEQ_K [ giga J per WEQ*yr] + Vraag_perWEQ_App [ giga J per WEQ*yr]) / 130
df_neighbourhood_properties["electricity_demand_per_m2_utility"] = df_neighbourhood_properties["electricity_demand_per_house"].apply(pd.to_numeric) / 130.0

## Adding additional (empty) columns

df_neighbourhood_properties['share_of_houses_demolished'] = 0
df_neighbourhood_properties['number_of_new_apartments'] = 0
df_neighbourhood_properties['number_of_new_terraced_houses'] = 0
df_neighbourhood_properties['number_of_new_detached_houses'] = 0
df_neighbourhood_properties['number_of_new_semi_detached_houses'] = 0
df_neighbourhood_properties['number_of_new_houses_unknown_type'] = 0
df_neighbourhood_properties['epi_of_new_houses'] = 0.9
df_neighbourhood_properties['size_of_new_houses'] = 100.0

## Drop unused columns
df_neighbourhood_properties.drop(['Vraag_perWEQ_K [ giga J per WEQ*yr]', 'Vraag_perWEQ_App [ giga J per WEQ*yr]', 'InStudieGebied?'], axis=1, inplace=True)

# Merging the dataframes
df_neighbourhoods = df_neighbourhood_list.merge(df_neighbourhood_properties, how='left', on='neighbourhood_code')

#========================= Neighbourhood percentage of heat network =======================

print('\nLoading data on heat network percentages\n')
heat_network_percentage_file = main_path / "input_data" / "existing_heat_network_share.csv"
df_heat_network_percentage = pd.read_csv(Path(heat_network_percentage_file), dtype={"BU_CODE": object, "P_STADVERW": object})

number_of_objects_with_heat_network = len(df_heat_network_percentage)
print("Found ", number_of_objects_with_heat_network, " neighbourhoods with a percentage defined.\n")

# removing redundant columns
print('Removing redundant columns')
keep = ['BU_CODE', 'P_STADVERW']
df_heat_network_percentage = df_heat_network_percentage[keep]
df_heat_network_percentage.set_index('BU_CODE', inplace=True)
df_heat_network_percentage.index.names = ['neighbourhood_code']

# Create column of percentage of heat networks for all neighbourhoods
df_neighbourhoods = df_neighbourhoods.merge(df_heat_network_percentage, how='left', on='neighbourhood_code')

# Add zero's to neighbourhoods that don't occur in df_heat_network_percentage
df_neighbourhoods = df_neighbourhoods.fillna(0)

# Rename column
df_neighbourhoods.rename(columns = {'P_STADVERW': 'existing_heat_network_share'}, inplace = True)



# export to CSV
print('Exporting results to CSV\n')
output_file = main_path / "input_data" / "neighbourhood_properties.csv"
df_neighbourhoods.to_csv(output_file)
print('Success! Results can be found in {}'.format(output_file))
