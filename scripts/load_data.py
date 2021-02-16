# system modules
import os
import sys
from pathlib import Path

# external modules
import csv
import math
import numpy as np
import pandas as pd
import pickle

# project modules
from HeatSource import HeatSource
from Neighbourhood import Neighbourhood
import config


def read_data(target_file):
    """
    Read input data from CSV into DataFrame
    """

    # Specify target file path
    target_path = (Path(__file__).resolve().parents[1] /
                   "input_data" / f"{config.current_project_name}")


    # Read csv into DataFrame
    data = pd.read_csv(target_path / target_file)

    return data


def initialise_neighbourhoods():
    """
    Initialise dictionary of neighbourhoods by their code (ID) and name
    """

    neighbourhoods = {}

    csv = config.current_project.NEIGHBOURHOOD_CSVS['list']

    initial_values = read_data(csv)

    for index, row in initial_values.iterrows():
        neighbourhoods[row['neighbourhood_code']] = Neighbourhood(
            row.to_dict())

    print('  - Initialised {} neighbourhoods with {}'.format(
        len(neighbourhoods), csv))

    return neighbourhoods


def update_neighbourhoods(neighbourhoods, csv):
    """
    Enrich the neighbourhoods with additional information read from the CSV
    """

    values = read_data(csv)

    count = 0

    for index, row in values.iterrows():
        try:
            neighbourhoods[row['neighbourhood_code']].update(row.to_dict())
            count += 1
        except KeyError:
            print(
                'KeyError processing {}'.format(row))
            sys.exit()

    print('  - Updated {} neighbourhoods with {}'.format(count, csv))

    return neighbourhoods


def remove_demolished_houses_from_housing_stock(neighbourhoods):
    """
    Based on information about a neighbourhood's demolition plans, remove the
    (to be) demolished houses from the housing stock.

    Assumption: demolition affects houses from selected cells equally.
    """

    neighbourhood_count = 0
    demolished_houses_count = 0.0

    selected_years = ['<1946', '1946-1974', '1975-1990']

    for code in neighbourhoods:
        housing_stock_matrix = neighbourhoods[code].housing_stock_matrix

        total_number_of_houses = neighbourhoods[code].number_of_houses()

        demolished_houses = (total_number_of_houses *
                             neighbourhoods[code].share_of_houses_demolished)

        houses_in_selected_cells = 0.0

        for housing_type, year_dicts in housing_stock_matrix.items():
            for year, properties in year_dicts.items():
                if year in selected_years:
                    houses_in_selected_cells += properties['aantal_woningen']

        if neighbourhoods[code].share_of_houses_demolished > 0.0:
            try:
                demolition_share = demolished_houses / houses_in_selected_cells

            except ZeroDivisionError:
                demolition_share = 0.0
                print(('Warning! Neighbourhood {} has a demolition share of {}'
                       ' but no houses!\n')
                      .format(code,
                              neighbourhoods[code].share_of_houses_demolished))

            if demolition_share > 1.0:
                print(('Warning! Neighbourhood {0}: The number of houses that '
                       'is supposed to be demolished ({1:.0f}) exceeds the '
                       'number of houses built in the years {2} ({3:.0f})\n')
                      .format(code, demolished_houses,
                              ','.join(selected_years),
                              houses_in_selected_cells))
                demolition_share = 1.0

            for housing_type, year_dicts in housing_stock_matrix.items():
                for year, properties in year_dicts.items():
                    if year in selected_years:
                        original_number_of_houses = properties['aantal_woningen']
                        properties['aantal_woningen'] *= (1 - demolition_share)
                        properties['aantal_kleine_woningen'] *= (1 - demolition_share)

                        demolished_houses_count += (original_number_of_houses -
                                                    properties['aantal_woningen'])

            neighbourhood_count += 1

            neighbourhoods[code].update(
                {'housing_stock_matrix': housing_stock_matrix})

    print('  - Demolished {} houses in {} neighbourhoods'
          .format(demolished_houses_count, neighbourhood_count))

    return neighbourhoods


def classify_new_houses_of_unknown_type(neighbourhoods):
    """
    If the type of the new houses is unknown, classify them based on the
    neighbourhood's current ratio of housing types.
    """

    for code in neighbourhoods:
        housing_stock_matrix = neighbourhoods[code].housing_stock_matrix

        total_number_of_houses = neighbourhoods[code].number_of_houses()

        for housing_type, year_dicts in housing_stock_matrix.items():

            formatted_type = (housing_type.lower()
                                          .replace(' ', '_')
                                          .replace('-', '_') + 's')

            number_of_houses = 0.0

            for year, properties in year_dicts.items():
                number_of_houses += properties['aantal_woningen']

            try:
                multiplication_factor = number_of_houses / total_number_of_houses

            except ZeroDivisionError:
                # If neighbourhood currently has no houses, divide new houses
                # evenly over 4 house types
                multiplication_factor = 0.25

            number_of_unknown_houses = neighbourhoods[code].number_of_new_houses_unknown_type

            new_number_of_houses = ((multiplication_factor *
                                     number_of_unknown_houses) +
                                    getattr(neighbourhoods[code],
                                            'number_of_new_{}'
                                            .format(formatted_type)))

            setattr(neighbourhoods[code],
                    'number_of_new_{}'.format(formatted_type),
                    new_number_of_houses)

    return neighbourhoods


def add_new_houses_to_housing_stock(neighbourhoods):
    """
    If the type of the new houses is known, add the number to the specified
    housing type
    """

    neighbourhood_list = []
    new_houses_count = 0.0

    neighbourhoods = classify_new_houses_of_unknown_type(neighbourhoods)

    for code in neighbourhoods:
        housing_stock_matrix = neighbourhoods[code].housing_stock_matrix

        for housing_type, year_dicts in housing_stock_matrix.items():
            if '>2010' not in year_dicts:
                housing_stock_matrix[housing_type]['>2010'] = {
                    'aantal_woningen': 0.0,
                    'aantal_kleine_woningen': 0.0,
                    'gem_epi': 0.0,
                    'gem_oppervlakte': 0.0
                }

            for year, properties in year_dicts.items():
                if year == '>2010':
                    formatted_type = (housing_type.lower()
                                                  .replace(' ', '_')
                                                  .replace('-', '_') + 's')

                    number_of_new_houses = getattr(neighbourhoods[code], 'number_of_new_{}'.format(formatted_type))
                    new_number_of_houses = properties['aantal_woningen'] + number_of_new_houses

                    if number_of_new_houses > 0.0:
                        properties['gem_epi'] = (((properties['aantal_woningen'] * properties['gem_epi']) +
                                                 (getattr(neighbourhoods[code], 'number_of_new_{}'.format(formatted_type)) * neighbourhoods[code].epi_of_new_houses)) /
                                                 new_number_of_houses)
                        properties['gem_oppervlakte'] = ((properties['aantal_woningen'] * properties['gem_oppervlakte'] +
                                                         (getattr(neighbourhoods[code], 'number_of_new_{}'.format(formatted_type)) * neighbourhoods[code].size_of_new_houses)) /
                                                         new_number_of_houses)
                        properties['aantal_woningen'] = new_number_of_houses

                        if neighbourhoods[code].size_of_new_houses <= 75.0:
                            properties['aantal_kleine_woningen'] = (properties['aantal_kleine_woningen'] +
                                                                    getattr(neighbourhoods[code], 'number_of_new_{}'.format(formatted_type)))

                        new_houses_count += number_of_new_houses

                        neighbourhood_list.append(code)

        neighbourhoods[code].update(
            {'housing_stock_matrix': housing_stock_matrix})

    print('  - Added {} new houses to {} neighbourhoods'.format(new_houses_count, len(set(neighbourhood_list))))

    return neighbourhoods


def update_neighbourhood_housing_stock(neighbourhoods, csv):
    """
    Describe method
    """

    values = read_data(csv)

    count = 0

    # Loop over all neighbourhoods
    for code in neighbourhoods:
        # Filter DataFrame rows for the current neighbourhood from the dataframe
        values_for_current_neighbourhood = values[values['buurtcode'] == code]

        # Initialising matrix
        housing_stock_matrix = {
            'Apartment': {},
            'Terraced house': {},
            'Semi-detached house': {},
            'Detached house': {}
        }

        # Initialise number of LT eligible houses and LT eligibility criteria
        number_of_lt_eligible_houses = 0

        # Transform the DataFrame into a list of dictionaries and loop over each row
        for row in values_for_current_neighbourhood.to_dict(orient='records'):
            # Filling matrix with types and year classes for this neighbourhood
            housing_stock_matrix[row['woningtype']][
                row['QI_bouwjaarklasse']] = {
                    'aantal_woningen': row['aantal_woningen'],
                    'aantal_kleine_woningen': row['aantal_kleine_woningen'],
                    'gem_epi': row['gem_epi'],
                    'gem_oppervlakte': row['gem_oppervlakte']
                }

        # Update neighbourhood with housing stock matrix
        neighbourhoods[code].update(
            {'housing_stock_matrix': housing_stock_matrix})
        # and number of LT eligible houses
        neighbourhoods[code].number_of_lt_eligible_houses = number_of_lt_eligible_houses

        count += 1

    print('  - Updated {} neighbourhoods with {}'.format(count, csv))

    return neighbourhoods


def update_neighbourhood_utility_stock(neighbourhoods, csv):
    """
    Describe method
    """

    values = read_data(csv)

    count = 0

    # Loop over all neighbourhoods
    for code in neighbourhoods:
        # Filter DataFrame rows for current neighbourhood from the dataframe
        values_for_current_neighbourhood = values[values['buurtcode'] == code]
        # Initialising matrix
        utility_stock_matrix = {'Small': {}, 'Medium': {}, 'Large': {}}

        # Transform the DataFrame into a list of dicts and loop over each row
        for row in values_for_current_neighbourhood.to_dict(orient='records'):
            # Filling matrix with types and size classes for this neighbourhood
            if row['aantal_gebouwen'] > 0:
                utility_stock_matrix[row['QI_oppervlakteklasse']][
                    row['QI_bouwjaarklasse']] = {
                        'aantal_gebouwen': row['aantal_gebouwen'],
                        'gem_epi': row['gem_epi'],
                        'totaal_oppervlakte': row['totaal_oppervlakte']
                    }

        # Update neighbourhood with housing stock matrix
        neighbourhoods[code].update(
            {'utility_stock_matrix': utility_stock_matrix})
        count += 1

    print('  - Updated {} neighbourhoods with {}'.format(count, csv))

    return neighbourhoods


def initialise_heat_sources(csv):
    """
    Initialise dictionary of heat sources by their ID and name
    """

    heat_sources = {}

    values = read_data(csv)

    for index, row in values.iterrows():
        heat_sources[row['source_id']] = HeatSource(row.to_dict())

    print('  - Initialised {} heat sources with {}'.format(
        len(heat_sources), csv))

    return heat_sources


def map_heat_sources_to_neighbourhoods(neighbourhoods, heat_sources,
                                       source_type):
    """
    Map the heat sources to neighbourhoods: for each neighbourhood, determine
    which sources are in range (and thereby possibly available to supply heat).
    """

    neighbourhood_dict = {}

    for code, neighbourhood in neighbourhoods.items():
        neighbourhood_dict[code] = []

    for code, source in heat_sources.items():
        try:
            neighbourhoods_in_range = source.neighbourhoods_in_range.split(',')

        except AttributeError:
            neighbourhoods_in_range = []

        for code in neighbourhoods_in_range:
            neighbourhood_dict[code].append(source.code)

    for code, neighbourhood in neighbourhoods.items():
        if source_type == 'ht_heat':
            neighbourhood.ht_sources_available = neighbourhood_dict[code]

        elif source_type == 'lt_heat':
            neighbourhood.lt_sources_available = neighbourhood_dict[code]

        elif source_type == 'geothermal':
            neighbourhood.geothermal_available = bool(neighbourhood_dict[code])

        elif source_type == 'teo':
            neighbourhood.teo_available = bool(neighbourhood_dict[code])

    return neighbourhoods


def save_objects(object, name):
    """
    Pickle the objects to the output data directory
    """

    filename = (Path(__file__).resolve().parents[1] / "output_data" /
                f"{config.current_project_name}" /
                f"{config.current_project.current_scenario_name}" /
                f"{name}.pkl")

    # Create file/folders if non-existent
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb') as output:
        pickle.dump(object, output, pickle.HIGHEST_PROTOCOL)


def export_data_to_csv(neighbourhoods):
    """
    Export the neighbourhood's properties to a CSV file in the output data
    directory
    """

    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "neighbourhoods_characteristics.csv")

    csv_columns = [
        'code', 'name', 'geo_coordinate',
        'number_of_house_equivalents_residences',
        'number_of_house_equivalents_utility', 'm2_of_utility',
        'total_heat_demand_of_residences', 'total_heat_demand_of_utility',
        'total_electricity_demand_of_residences',
        'total_electricity_demand_of_utility', 'geothermal_available', 'teo_available',
        'ht_sources_available', 'lt_sources_available', 'preference_W_MTHT',
        'preference_H', 'preference_E', 'elegible_W_LT', 'force_heat_network'
    ]

    # Write the neighbourhood objects to csv file rows
    with open(path, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
        writer.writeheader()
        for neighbourhood in neighbourhoods.values():
            for preference in neighbourhood.heating_option_preference:
                if preference[0] == 'W_MTHT':
                    preference_W_MTHT = preference[1]
                elif preference[0] == 'H':
                    preference_H = preference[1]
                elif preference[0] == 'E':
                    preference_E = preference[1]

            characteristics = {
                'code':
                neighbourhood.code,
                'name':
                neighbourhood.name,
                'geo_coordinate':
                neighbourhood.geo_coordinate,
                'number_of_house_equivalents_residences':
                neighbourhood.number_of_houses(),
                'number_of_house_equivalents_utility':
                (neighbourhood.m2_of_utility() *
                 config.current_project.KEY_FIGURES['m2_utility_to_house_equivalents']),
                'm2_of_utility':
                neighbourhood.m2_of_utility(),
                'total_heat_demand_of_residences':
                neighbourhood.total_heat_demand_of_residences(),
                'total_heat_demand_of_utility':
                neighbourhood.total_heat_demand_of_utility(),
                'total_electricity_demand_of_residences':
                neighbourhood.total_electricity_demand_of_residences(),
                'total_electricity_demand_of_utility':
                neighbourhood.total_electricity_demand_of_utility(),
                'geothermal_available':
                neighbourhood.geothermal_available,
                'teo_available':
                neighbourhood.teo_available,
                'ht_sources_available':
                neighbourhood.ht_sources_available,
                'lt_sources_available':
                neighbourhood.lt_sources_available,
                'preference_W_MTHT':
                preference_W_MTHT,
                'preference_H':
                preference_H,
                'preference_E':
                preference_E,
                'elegible_W_LT':
                neighbourhood.lt_elegible,
                'force_heat_network':
                neighbourhood.force_heat_network
            }
            writer.writerow(characteristics)


def initialise_neighbourhoods_and_heat_sources():
    """
    Main method in which all neighbourhoods and heat sources are initialised
    and updated (or enriched) based on the input data (CSV files specified in
    the config file)
    """

    print('\nInitialising neighbourhoods and heat sources..')

    # Initialise neighbourhoods
    neighbourhoods = initialise_neighbourhoods()

    # Update neighbourhoods based on additional csv files
    csvs = config.current_project.NEIGHBOURHOOD_CSVS['properties']
    for csv in csvs:
        neighbourhoods = update_neighbourhoods(neighbourhoods, csv)

    # Update neighbourhoods based on housing and utility stock csv files
    neighbourhoods = update_neighbourhood_housing_stock(
        neighbourhoods, config.current_project.NEIGHBOURHOOD_CSVS['housing_stock'])

    neighbourhoods = remove_demolished_houses_from_housing_stock(neighbourhoods)
    neighbourhoods = add_new_houses_to_housing_stock(neighbourhoods)

    neighbourhoods = update_neighbourhood_utility_stock(
        neighbourhoods, config.current_project.NEIGHBOURHOOD_CSVS['utility_stock'])

    # Determine the heating option preferences for all neighbourhoods
    for neighbourhood in neighbourhoods.values():
        neighbourhood.determine_heating_option_preference()

        # Check if confidences of heating options sums up to 1
        sum_of_confidences = sum(n for _, n in neighbourhood.heating_option_preference)
        if not math.isclose(sum_of_confidences, 1.):
            if sum_of_confidences != 0.:
                print('\nWARNING! For {}, the confidences of the heating options = {} != 1.'.format(
                    neighbourhood.code, sum_of_confidences))

    # Initialise HT sources and map to neighbourhoods
    ht_sources = initialise_heat_sources(config.current_project.current_scenario['ht_heat'])
    neighbourhoods = map_heat_sources_to_neighbourhoods(
        neighbourhoods, ht_sources, 'ht_heat')

    # Initialise LT sources and map to neighbourhoods
    lt_sources = initialise_heat_sources(config.current_project.current_scenario['lt_heat'])
    neighbourhoods = map_heat_sources_to_neighbourhoods(
        neighbourhoods, lt_sources, 'lt_heat')

    # Initialise geothermal sources and map to neighbourhoods
    geothermal_sources = initialise_heat_sources(
        config.current_project.current_scenario['geothermal'])
    neighbourhoods = map_heat_sources_to_neighbourhoods(
        neighbourhoods, geothermal_sources, 'geothermal')

    # Initialise TEO sources and map to neighbourhoods
    teo_sources = initialise_heat_sources(config.current_project.current_scenario['teo'])
    neighbourhoods = map_heat_sources_to_neighbourhoods(
    neighbourhoods, teo_sources, 'teo')

    # Pickle neighbourhoods and heat sources
    # Geothermal is not saved as only availability ('yes'/'no') is relevant
    # (which is saved in the neighbourhood objects)
    save_objects(neighbourhoods, 'neighbourhoods')
    save_objects(ht_sources, 'ht_sources')
    save_objects(lt_sources, 'lt_sources')

    # Export neighbourhood characteristics to CSV
    export_data_to_csv(neighbourhoods)

    print('Done!')


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('The following arguments were expected: load_data.py <PROJECT> <SCENARIO>')
    else:
        config.set_current_project(sys.argv[1])
        config.current_project.set_current_scenario(sys.argv[2])
        initialise_neighbourhoods_and_heat_sources()
