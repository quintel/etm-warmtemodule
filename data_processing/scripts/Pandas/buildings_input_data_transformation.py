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
main_path = Path(__file__).resolve().parents[2] # data_processing folder
building_stock_file = main_path / "BAG" / "buildings" / "BAG20200101_building_stock_2019buurtenOBgebied.csv"

print('\nLoading buildings stock data\n')
df_building_stock = pd.read_csv(Path(building_stock_file), dtype={"BU_CODE": object, "BU_NAAM": object})

initial_number_of_objects = len(df_building_stock)

# drop buildings
print('Dropping objects without neighbourhood code\n')
df_building_stock = df_building_stock[~df_building_stock['BU_CODE'].isna()]

# save total number of objects
total_number_of_objects = len(df_building_stock)
print('Dropped {} objects without neighbourhood code, continuing analysis with {} objects\n'.format(initial_number_of_objects - total_number_of_objects, total_number_of_objects))

df_building_stock['postcode'], df_building_stock['huisnummer'], df_building_stock['toevoeging'] = df_building_stock['LABEL'].str.split('_', 2).str

# remove redundant columns
print('Removing redundant columns\n')
keep = ['IDENTIFICA', 'postcode', 'huisnummer', 'toevoeging', 'OPPERVLAKT', 'BOUWJAAR', 'BOUWJAARUT', 'GEBRUIKSDO', 'BU_CODE', 'BU_NAAM']
df_building_stock = df_building_stock[keep]

# Load preliminary energy label mapping
print('Loading preliminary energy label mapping\n')
generic_label_file = main_path / "BAG" / "buildings" / "vesta_generic_labels_buildings.csv"
generic_label = pd.read_csv(generic_label_file)
generic_label.columns = ['gebruiksdoel', 'BOUWJAARUT', 'prelim_energy_index', 'prelim_energy_label']

# Add preliminary energy label and energy performance index to each object
print('Adding energy labels and performance index to objects\n')
df_building_stock = df_building_stock.merge(generic_label, how='left', left_on=['GEBRUIKSDO', 'BOUWJAARUT'], right_on=['gebruiksdoel', 'BOUWJAARUT'])

check_number_of_objects(len(df_building_stock), total_number_of_objects)

# Load energy label database with 'final' energy labels (EP-online)
print('Loading energy label database\n')
ep_online_file = main_path / "BAG" / "general" / "ep_online_v20201001.csv"
ep_online = pd.read_csv(ep_online_file, sep=';')

keep = ['Pand_postcode', 'Pand_huisnummer', 'Pand_huisnummer_toev', 'Meting_geldig_tot', 'Pand_energieklasse', 'Pand_energieprestatieindex']
ep_online = ep_online[keep]
ep_online.columns = ['postcode', 'huisnummer', 'toevoeging', 'Meting_geldig_tot', 'Pand_energieklasse', 'Pand_energieprestatieindex']

df_building_stock = df_building_stock.astype({'huisnummer': float})

# some postcode/huisnummer/toevoeging combinations appear multiple times in the data. To avoid creating duplicates when merging with housing stock data, we sort the data by expiry date of the energy label. If a building occurs more than once we drop the one with the earliest expiry date
print('Deleting duplicates from energy label database\n')
ep_online = ep_online.sort_values('Meting_geldig_tot', ascending=False).drop_duplicates(subset=['postcode', 'huisnummer', 'toevoeging'], keep='first')

# Add final energy label / performance index to object if available
print('Adding "final" energy label to objects if available\n')
df_building_stock = df_building_stock.merge(ep_online, how='left', on=['postcode', 'huisnummer', 'toevoeging'])

check_number_of_objects(len(df_building_stock), total_number_of_objects)

# Load label / energy performance index mapping
energy_index_file = main_path / "BAG" / "general" / "epi_per_label.csv"
estimated_e_index = pd.read_csv(energy_index_file)

# Add (estimated) energy performance index to each object with a final label but no epi
df_building_stock = df_building_stock.merge(estimated_e_index, how='left', left_on='Pand_energieklasse', right_on='elabel')

check_number_of_objects(len(df_building_stock), total_number_of_objects)

# Add 'epi' column based on best available epi data
# Epi data directly from EP-online is best
# If that is missing but a label from EP-online is available, we use that
# Else we use the preliminary epi
print('Adding column with most accurate energy performance indicator\n')
df_building_stock["epi"] = df_building_stock["Pand_energieprestatieindex"].fillna(df_building_stock["estim_index"].fillna(df_building_stock["prelim_energy_index"]))

# Add energy label column based on best available data
# Data from EP-online is best
# Else use preliminary label
print('Adding column with most accurate energy label\n')
df_building_stock["energielabel"] = df_building_stock["Pand_energieklasse"].fillna(df_building_stock["prelim_energy_label"])

# Add weighted epi column
print('Adding column with weighted energy performance indicator based on object size\n')
df_building_stock['weighted_epi'] = df_building_stock['epi'] * df_building_stock['OPPERVLAKT']

building_types_file = main_path / "BAG" / "buildings" / "building_types.csv"
gebouwtype_indeling = pd.read_csv(building_types_file)

# add buildings types
print('Adding buildings types\n')
df_building_stock = df_building_stock.merge(gebouwtype_indeling, how='left', left_on='GEBRUIKSDO', right_on='building_type_cat')

check_number_of_objects(len(df_building_stock), total_number_of_objects)

# clean up dataframe
print('Cleaning up dataframe\n')
keep = ['postcode', 'huisnummer', 'toevoeging', 'building_function', 'GEBRUIKSDO', 'OPPERVLAKT', 'BOUWJAAR', 'BOUWJAARUT', 'epi', 'energielabel', 'weighted_epi', 'Pand_energieprestatieindex', 'Pand_energieklasse', 'prelim_energy_index', 'prelim_energy_label', 'BU_CODE', 'BU_NAAM']
df_building_stock = df_building_stock[keep]
df_building_stock.columns = ['postcode', 'huisnummer', 'toevoeging', 'gebruiksdoel', 'gebruiksdoel_klasse', 'oppervlakte', 'bouwjaar',  'bouwjaarklasse', 'epi', 'energielabel', 'gewogen_epi', 'ep-online_epi', 'ep-online_label', 'vesta_epi', 'vesta_label', 'buurtcode', 'buurtnaam']

# remove industry objects
print('Removing objects with type="industry"\n')
df_building_stock = df_building_stock[~df_building_stock['gebruiksdoel'].isin(['industrie', 'overig'])]

print('Removed {} objects with buildings type "industry" or "other"\n'.format(total_number_of_objects - len(df_building_stock)))

"""
Grouping objects
- Define size bins
- Group by neighbourhood / type / size
"""

# define QI_oppervlakteklasse. If building size >= 0, QI_oppervlakteklasse is 'Small' etc.
size_bins = [0, 200, 2000]
size_names = ['Small', 'Medium', 'Large']
d = dict(enumerate(size_names, 1))
df_building_stock['QI_oppervlakteklasse'] = np.vectorize(d.get)(np.digitize(df_building_stock['oppervlakte'], size_bins))

# define QI_bouwjaarklaase.
year_bins = [0, 1991, 2001]
year_names = ['<1991', '1991-2000', '>2000']
e = dict(enumerate(year_names, 1))
df_building_stock['QI_bouwjaarklasse'] = np.vectorize(e.get)(np.digitize(df_building_stock['bouwjaar'], year_bins))

# convert new attributes to categorical (for sorting purposes)
df_building_stock['QI_oppervlakteklasse'] = pd.Categorical(df_building_stock['QI_oppervlakteklasse'], size_names)
df_building_stock['QI_bouwjaarklasse'] = pd.Categorical(df_building_stock['QI_bouwjaarklasse'], year_names)

# define how each column should be aggregated
aggregations = {
    "gebruiksdoel": "count",
    "oppervlakte": "sum",
    "gewogen_epi": "sum",
    "buurtnaam": "first"
}

# group objects by neighbourhood / buildings type / building size class
print('Grouping objects by neighbourhood / building size class / year class \n')
df_building_stock_neighbourhood = df_building_stock.groupby(['buurtcode', 'QI_oppervlakteklasse', 'QI_bouwjaarklasse'], observed=True).agg(aggregations)

df_building_stock_neighbourhood.head(100)

check_number_of_objects(df_building_stock_neighbourhood['gebruiksdoel'].sum(), len(df_building_stock))

print('Grouped {} objects (({} m2))\nNumber of neighbourhoods: {}\n'.format(df_building_stock_neighbourhood['gebruiksdoel'].sum(), df_building_stock_neighbourhood['oppervlakte'].sum(), df_building_stock.reset_index().buurtcode.nunique()))

print('Adding average energy performance per category\n')
df_building_stock_neighbourhood['mean_epi'] = df_building_stock_neighbourhood['gewogen_epi'] / df_building_stock_neighbourhood['oppervlakte']

keep = ['gebruiksdoel', 'oppervlakte', 'mean_epi', 'buurtnaam']
df_building_stock_neighbourhood = df_building_stock_neighbourhood[keep]

# rename columns
df_building_stock_neighbourhood = df_building_stock_neighbourhood.rename(columns={'gebruiksdoel': 'aantal_gebouwen', 'oppervlakte': 'totaal_oppervlakte', 'mean_epi': 'gem_epi'})

# export to CSV
print('Exporting results to CSV\n')
output_file = main_path.parent / "input_data" / "building_stock_size_year_per_neighbourhood.csv"
df_building_stock_neighbourhood.to_csv(output_file)
print('Success! Results can be found in {}'.format(output_file))
