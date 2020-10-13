#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from pathlib import Path


def check_number_of_objects(current_number_of_objects, intended_number_of_objects):
    if current_number_of_objects != intended_number_of_objects:
        print('Something went wrong, the total number of objects has changed. Total was {} but is now {}\n Aborting..'.format(intended_number_of_objects, current_number_of_objects))
        exit()


"""
Transforming raw BAG data
- Clean up input file
- Determine energy label and performance index
"""
# load raw data
# When exporting to .py file, remove "" from "__file__"
main_path = Path(__file__).resolve().parents[2]  # data_processing folder
housing_stock_file = main_path / "BAG" / "households" / "BAG_housing_stock.csv"

print('\nLoading housing stock data\n')
df_housing_stock = pd.read_csv(Path(housing_stock_file), dtype={"BU_CODE": object, "BU_NAAM": object})

initial_number_of_objects = len(df_housing_stock)

# drop buildings
print('Dropping objects without neighbourhood code\n')
df_housing_stock = df_housing_stock[~df_housing_stock['BU_CODE'].isna()]

# save total number of objects
total_number_of_objects = len(df_housing_stock)
print('Dropped {} objects without neighbourhood code, continuing analysis with {} objects\n'.format(initial_number_of_objects - total_number_of_objects, total_number_of_objects))

# drop buildings
print('Dropping objects without housing type\n')
df_housing_stock = df_housing_stock[df_housing_stock['WONINGTYPE'] != 255]

# save total number of objects
total_number_of_objects_after_housing_type_drop = len(df_housing_stock)
print('Dropped {} objects without housing type, continuing analysis with {} objects\n'.format(total_number_of_objects - total_number_of_objects_after_housing_type_drop, total_number_of_objects_after_housing_type_drop))
df_housing_stock['postcode'], df_housing_stock['huisnummer'], df_housing_stock['toevoeging'] = df_housing_stock['LABEL'].str.split('_', 2).str

# removing redundant columns
print('Removing redundant columns\n')
keep = ['IDENTIFICA', 'ENERGIELAB', 'POSTCODE', 'huisnummer', 'toevoeging', 'OPPERVLAKT', 'BOUWJAAR', 'BOUWJAARWO', 'WONINGTYPE', 'BU_CODE', 'BU_NAAM']
df_housing_stock = df_housing_stock[keep]
df_housing_stock.set_index('IDENTIFICA', inplace=True)

# Load preliminary energy label mapping
print('Loading preliminary energy label mapping\n')
generic_label_file = main_path / "BAG" / "households" / "vesta_generic_labels_households.csv"
generic_label = pd.read_csv(generic_label_file)
generic_label.columns = ['WONINGTYPE', 'BOUWJAARWO', 'prelim_energy_index', 'prelim_energy_label']

# Add preliminary energy label and energy performance index to each object
print('Adding energy labels and performance index to objects\n')
df_housing_stock = df_housing_stock.merge(generic_label, how='left', left_on=['WONINGTYPE', 'BOUWJAARWO'], right_on=['WONINGTYPE', 'BOUWJAARWO'])

check_number_of_objects(len(df_housing_stock), total_number_of_objects_after_housing_type_drop)

# Load energy label database with 'final' energy labels (EP-online)
print('Loading energy label database\n')
ep_online_file = main_path / "BAG" / "general" / "ep_online_v20190901.csv"
ep_online = pd.read_csv(ep_online_file, sep=';')

keep = ['Pand_postcode', 'Pand_huisnummer', 'Pand_huisnummer_toev', 'Meting_geldig_tot', 'Pand_energieklasse', 'Pand_energieprestatieindex']
ep_online = ep_online[keep]
ep_online.columns = ['postcode', 'huisnummer', 'toevoeging', 'Meting_geldig_tot', 'Pand_energieklasse', 'Pand_energieprestatieindex']

df_housing_stock = df_housing_stock.astype({'huisnummer': float})

# some postcode/huisnummer/toevoeging combinations appear multiple times in the data. To avoid creating duplicates when merging with housing stock data, we sort the data by expiry date of the energy label. If a building occurs more than once we drop the one with the earliest expiry date
print('Deleting duplicates from energy label database\n')
ep_online = ep_online.sort_values('Meting_geldig_tot', ascending=False).drop_duplicates(subset=['postcode', 'huisnummer', 'toevoeging'], keep='first')

# Add final energy label / performance index to object if available
print('Adding "final" energy label to objects if available\n')
df_housing_stock = df_housing_stock.merge(ep_online, how='left', left_on=['POSTCODE', 'huisnummer', 'toevoeging'], right_on=['postcode', 'huisnummer', 'toevoeging'])

check_number_of_objects(len(df_housing_stock), total_number_of_objects_after_housing_type_drop)

# Load label / energy performance index mapping
energy_index_file = main_path / "BAG" / "general" / "epi_per_label.csv"
estimated_e_index = pd.read_csv(energy_index_file)

# Add (estimated) energy performance index to each object with a final label but no epi
df_housing_stock = df_housing_stock.merge(estimated_e_index, how='left', left_on='Pand_energieklasse', right_on='elabel')

check_number_of_objects(len(df_housing_stock), total_number_of_objects_after_housing_type_drop)

# Add 'epi' column based on best available epi data
# Epi data directly from EP-online is best
# If that is missing but a label from EP-online is available, we use that
# Else we use the preliminary epi
print('Adding column with most accurate energy performance indicator\n')
df_housing_stock["epi"] = df_housing_stock["Pand_energieprestatieindex"].fillna(df_housing_stock["estim_index"].fillna(df_housing_stock["prelim_energy_index"]))

# Add energy label column based on best available data
# Data from EP-online is best
# Else use preliminary label
print('Adding column with most accurate energy label\n')
df_housing_stock["energielabel"] = df_housing_stock["Pand_energieklasse"].fillna(df_housing_stock["prelim_energy_label"])

housing_types_file = main_path / "BAG" / "households" / "housing_types.csv"
woningtype_indeling = pd.read_csv(housing_types_file)

# add housing types
print('Adding housing types\n')
df_housing_stock = df_housing_stock.merge(woningtype_indeling, how='left', left_on='WONINGTYPE', right_on='wo_type_cat')

df_housing_stock[df_housing_stock.woningtype.isna()]
check_number_of_objects(len(df_housing_stock), total_number_of_objects_after_housing_type_drop)

# add column for small houses (1 if small, 0 if not)
df_housing_stock['kleine_woning'] = np.where(df_housing_stock['OPPERVLAKT'] < 75.0, 1, 0)

# clean up dataframe
print('Cleaning up dataframe\n')
keep = ['POSTCODE', 'huisnummer', 'toevoeging',  'woningtype', 'WONINGTYPE', 'BOUWJAAR', 'BOUWJAARWO', 'OPPERVLAKT', 'kleine_woning', 'epi', 'energielabel', 'Pand_energieprestatieindex', 'Pand_energieklasse', 'prelim_energy_index', 'prelim_energy_label', 'BU_CODE', 'BU_NAAM']
df_housing_stock = df_housing_stock[keep]
df_housing_stock.columns = ['postcode', 'huisnummer', 'toevoeging', 'woningtype', 'woningtype_klasse', 'bouwjaar', 'bouwjaarklasse', 'oppervlakte', 'kleine_woning', 'epi', 'energielabel', 'ep-online_epi', 'ep-online_label', 'vesta_epi', 'vesta_label', 'buurtcode', 'buurtnaam']

check_number_of_objects(len(df_housing_stock), total_number_of_objects_after_housing_type_drop)

"""
Grouping objects
- Define size bins
- Group by neighbourhood / type / construction year
"""

# change 'corner house' residences to 'terraced house'
number_of_corner_houses = len(df_housing_stock[df_housing_stock.woningtype == 'Corner house'])
df_housing_stock.loc[df_housing_stock.woningtype == 'Corner house', 'woningtype'] = 'Terraced house'
print("Change housing type of {} objects from 'corner house' to 'terraced house'\n".format(number_of_corner_houses))

# define QI_bouwjaarklasse. If bouwjaar >= 0, QI_bouwjaarklasse is '<1946' etc.
bins = [0, 1946, 1975, 1991, 2001, 2011]
names = ['<1946', '1946-1974', '1975-1990', '1991-2000', '2001-2010', '>2010']

d = dict(enumerate(names, 1))
df_housing_stock['QI_bouwjaarklasse'] = np.vectorize(d.get)(np.digitize(df_housing_stock['bouwjaar'], bins))

# convert QI_bouwjaarklasse to categorical (for sorting purposes)
df_housing_stock['QI_bouwjaarklasse'] = pd.Categorical(df_housing_stock['QI_bouwjaarklasse'], ['<1946', '1946-1974', '1975-1990', '1991-2000', '2001-2010', '>2010'])
df_housing_stock['woningtype'].unique()

# aggregate data on neighbourhood level. For each <neighbourhood, residence type, year of construction class> class we get 1 data row
# For each class we want to know how many residences are part of that class, the mean energy efficiency, the mean size and the neighbourhood name
aggregations = {
    "woningtype": "count",
    "epi": "mean",
    "oppervlakte": "mean",
    "kleine_woning": "sum",
    "buurtnaam": "first"
}

# group objects by neighbourhood / housing type / construction year class
print('Grouping objects by neighbourhood / housing type / construction year class\n')

df_housing_stock_neighbourhood = df_housing_stock.groupby(['buurtcode', 'woningtype', 'QI_bouwjaarklasse'], observed=True).agg(aggregations)
check_number_of_objects(df_housing_stock_neighbourhood['woningtype'].sum(), len(df_housing_stock))
print('Grouped {} objects\nNumber of neighbourhoods: {}\n'.format(df_housing_stock_neighbourhood['woningtype'].sum(), df_housing_stock.reset_index().buurtcode.nunique()))

# rename columns
df_housing_stock_neighbourhood = df_housing_stock_neighbourhood.rename(columns={'woningtype': 'aantal_woningen', 'epi': 'gem_epi', 'oppervlakte': 'gem_oppervlakte', 'kleine_woning': 'aantal_kleine_woningen'})

# export to CSV
print('Exporting results to CSV\n')
output_file = main_path.parent / "input_data" / "housing_stock_type_year_per_neighbourhood.csv"
df_housing_stock_neighbourhood.to_csv(output_file)
print('Success! Results can be found in {}'.format(output_file))
