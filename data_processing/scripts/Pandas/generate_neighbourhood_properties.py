#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from pathlib import Path

# When exporting to .py file, remove "" from "__file__"
main_path = Path(__file__).resolve().parents[3]  # data_processing folder

#========================== Neighbourhood list ==================================

print('\nLoading complete list of neighbourhoods\n')
neighbourhood_list_file = main_path / "input_data" / "neighbourhoods_OB2020.csv"
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
neighbourhood_properties_file = main_path / "input_data" / "sample" / "neighbourhood_properties.csv"
df_neighbourhood_properties = pd.read_csv(Path(neighbourhood_properties_file), dtype=object)

number_of_properties_objects = len(df_neighbourhood_properties)
print("Found ", number_of_properties_objects, " neighbourhoods with additional properties")

df_neighbourhood_properties.set_index('neighbourhood_code', inplace=True)

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
df_neighbourhoods.rename(columns = {'P_STADVERW': 'percentage_of_heat_networks'}, inplace = True)

# export to CSV
print('Exporting results to CSV\n')
output_file = main_path / "input_data" / "neighbourhood_properties.csv"
df_neighbourhoods.to_csv(output_file)
print('Success! Results can be found in {}'.format(output_file))
