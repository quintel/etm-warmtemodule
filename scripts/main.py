# system modules
import os
import sys

# external modules
import csv
import numpy as np
import pickle
import requests
from pathlib import Path

# project modules
from Bookkeeper import Bookkeeper
from classify_neighbourhoods import (apply_electricity_decision_tree,
                                     apply_heat_decision_tree,
                                     apply_hybrid_decision_tree,
                                     apply_pre_analysis)
from load_data import initialise_neighbourhoods_and_heat_sources
import config
from post_analysis import flip_LT_eligible_neighbourhoods
from run_tests import run_all_tests


def load_neighbourhoods():
    # Load pickled neighbourhood objects (cached data)
    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}"
            / "neighbourhoods.pkl")

    with open(path, 'rb') as input:
        neighbourhoods = pickle.load(input)

    return neighbourhoods


def load_ht_sources():
    # Load pickled HT sources objects (cached data)
    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}"
            / "ht_sources.pkl")

    with open(path, 'rb') as input:
        ht_sources = pickle.load(input)

    return ht_sources


def load_lt_sources():
    # Load pickled LT sources objects (cached data)
    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "lt_sources.pkl")

    with open(path, 'rb') as input:
        lt_sources = pickle.load(input)

    return lt_sources


def apply_decision_trees(sorted_neighbourhoods, heat_sources, bookkeeper):
    """
    Pre-analysis,
    First preference decision tree,
    Second preference decision tree
    """

    # Run pre-analysis for all neighbourhoods
    number_of_assigned_neighbourhoods = 0

    for code, neighbourhood in sorted_neighbourhoods.items():
        apply_pre_analysis(neighbourhood, heat_sources, bookkeeper)

        # If the neighbourhood has been assigned a heating option, count it
        if neighbourhood.assigned_heating_option:
            neighbourhood.stage_of_assignment = 'pre-analysis'
            number_of_assigned_neighbourhoods += 1

            # Determine confidence for assigned heating option
            neighbourhood.confidence = config.current_project.ASSUMPTIONS[
                'pre_analysis_confidence']

            # print("{} ({}): {}, {} (confidence: {})".format(
            #     neighbourhood.name, neighbourhood.code,
            #     neighbourhood.assigned_heating_option,
            #     neighbourhood.assigned_heat_source,
            #     round(neighbourhood.confidence,2)))

    print("\nPRE-ANALYSIS: [{}/{}] neighbourhoods have been assigned "
          "a heating option".format(number_of_assigned_neighbourhoods,
                                    len(sorted_neighbourhoods)))

    # Loop twice over all neighbourhoods in order to assign heating options.
    # 1) Use the first loop to assign the neighbourhoods' first preferences. If
    # that's not possible, don't assign any option yet.
    # 2) Use the second loop for all unassigned neighbourhoods to assign their
    # second preference. If that's not possible, assign "E".
    for i in [0, 1]:
        # Sort neighbourhoods
        neighbourhoods = sorted_neighbourhoods
        sorted_neighbourhoods = {}
        # First iteration: sort on first preference percentage
        if i == 0:
            key = lambda x: x.heating_option_preference[0][1]
        # Second iteration: sort on first + second preference percentage
        elif i == 1:
            key = lambda x: (x.heating_option_preference[0][1] + x.
                             heating_option_preference[1][1])
        # Create new dictionary to store the sorted neighbourhoods
        for neighbourhood in sorted(neighbourhoods.values(),
                                    key=key,
                                    reverse=True):
            sorted_neighbourhoods[neighbourhood.code] = neighbourhood

        for code, neighbourhood in sorted_neighbourhoods.items():
            # If the neighbourhood has not been assigned a heating option yet,
            if not neighbourhood.assigned_heating_option:
                # If the neighbourhood's preference is "E",
                if neighbourhood.heating_option_preference[i][0] == 'E':
                    # Apply electricity decision tree to neighbourhood
                    apply_electricity_decision_tree(neighbourhood,
                                                    heat_sources, bookkeeper)

                # Else if the neighbourhood's preference is "W",
                elif neighbourhood.heating_option_preference[i][0] == 'W':
                    # Apply electricity decision tree to neighbourhood
                    apply_heat_decision_tree(neighbourhood, heat_sources,
                                             False, i == 1, bookkeeper)

                # Else if the neighbourhood's preference is "H",
                elif neighbourhood.heating_option_preference[i][0] == 'H':
                    # Apply hybrid decision tree to neighbourhood
                    apply_hybrid_decision_tree(neighbourhood, heat_sources,
                                               i == 1, bookkeeper)

                # If the neighbourhood has been assigned a heating option,
                # count it
                if neighbourhood.assigned_heating_option:
                    neighbourhood.stage_of_assignment = 'iteration {}'.format(
                        i + 1)
                    number_of_assigned_neighbourhoods += 1

                    tuple_position = [i for i, v in enumerate(neighbourhood.heating_option_preference) if v[0] == neighbourhood.assigned_heating_option]
                    # Determine confidence for assigned heating option
                    neighbourhood.confidence = neighbourhood.heating_option_preference[tuple_position[0]][1]

                    # print("{} ({}): {}, {} (confidence: {})".format(
                    #     neighbourhood.name, neighbourhood.code,
                    #     neighbourhood.assigned_heating_option,
                    #     neighbourhood.assigned_heat_source,
                    #     round(neighbourhood.confidence, 2)))

                else:
                    continue
                    print("{} ({}): undecided".format(neighbourhood.name,
                                                      neighbourhood.code))

        print("\nITERATION {}: [{}/{}] neighbourhoods have been assigned "
              "a heating option".format(i + 1,
                                        number_of_assigned_neighbourhoods,
                                        len(neighbourhoods)))

    # Check if all neighbourhoods have been assigned
    if number_of_assigned_neighbourhoods != len(sorted_neighbourhoods):
        print("\nERROR: some neighbourhoods are still undecided!")

        # If there are still neighbourhoods undecided, print the neighbourhoods
        # names and code
        for code, neighbourhood in sorted_neighbourhoods.items():
            if not neighbourhood.assigned_heating_option:
                print("  - {} ({})".format(neighbourhood.name,
                                           neighbourhood.code))
    return


def determine_distance_from_neighbourhood_to_source(neighbourhoods, heat_sources):
    """
    Determine the (Euclidean) distance from a neighbourhood to a (residual)
    heat source
    """

    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "distance_from_neighbourhood_to_source.csv")

    csv_columns = ['neighbourhood_code', 'heat_source_code', 'heat_source_name', 'distance_in_m']

    # Write the distances to csv file rows
    with open(path, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
        writer.writeheader()

        for code, neighbourhood in neighbourhoods.items():
            # Check if a heat source has been assigned to the neighbourhood
            assigned_heat_source_code = neighbourhood.assigned_heat_source

            # If so, find the corresponding heat source object
            if assigned_heat_source_code:
                if assigned_heat_source_code != "geothermal":
                    heat_type = assigned_heat_source_code[0:2]
                    assigned_heat_source = heat_sources[heat_type][assigned_heat_source_code]

                    # and determine the distance to the heat source
                    distance_to_heat_source = np.linalg.norm(
                        np.array(neighbourhood.geo_coordinate) -
                        np.array(assigned_heat_source.geo_coordinate))

                    writer.writerow({
                        'neighbourhood_code': code,
                        'heat_source_code': assigned_heat_source_code,
                        'heat_source_name': assigned_heat_source.name,
                        'distance_in_m': distance_to_heat_source
                    })


def export_neighbourhood_results_to_csv(neighbourhoods):
    """
    Export the neighbourhood attributes and results to a CSV file in the output
    data directory
    """

    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "neighbourhoods_output.csv")

    # Read the Neighbourhood attributes of the first neighbourhood into the
    # csv_columns variable
    for neighbourhood in neighbourhoods.values():
        csv_columns = list(neighbourhood.__dict__.keys())
        break

    # Write the neighbourhood objects to csv file rows
    with open(path, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
        writer.writeheader()
        for neighbourhood in neighbourhoods.values():
            writer.writerow(neighbourhood.__dict__)


def export_heat_source_results_to_csv(heat_sources):
    """
    Export the heat source attributes and results to a CSV file in the output
    data directory
    """

    for heat_type in ['HT', 'LT']:
        path = (Path(__file__).resolve().parents[1] / "output_data" /
                f"{config.current_project_name}" /
                f"{config.current_project.current_scenario_name}" /
                f"{heat_type}_sources_output.csv")

        # Read the HeatSource attributes of the first heat source into the
        # csv_columns variable
        for source in heat_sources[heat_type].values():
            csv_columns = list(source.__dict__.keys())
            break

        # Write the neighbourhood objects to csv file rows
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            writer.writeheader()
            for source in heat_sources[heat_type].values():
                writer.writerow(source.__dict__)


def save_objects(name, object):
    filename = (Path(__file__).resolve().parents[1] / "output_data" /
                f"{config.current_project_name}" /
                f"{config.current_project.current_scenario_name}" /
                f"{name}.pkl")

    # Create file/folders if non-existent
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb') as output:
        pickle.dump(object, output, pickle.HIGHEST_PROTOCOL)


def main(args):
    """
    Before running this script, make sure you have initialised neighbourhood
    objects, by running the load_data.py script.

    Run python3 main.py <project_name> <scenario_name> <optional: 'refresh'>
    in your terminal, where <project_name> is the name of a config file in the
    config_files folder (e.g. res_groningen) and <scenario_name> is the name of
    a scenario within that file, e.g. scenario_1.
    """
    try:
        config.set_current_project(args[0])

    except BaseException:
        print('\nWARNING! No (valid) project has been specified.')
        return

    # Determine scenario based on the user input
    try:
        print(args[1])
        config.current_project.set_current_scenario(args[1])

    except BaseException:
        print('\nWARNING! No (valid) scenario has been specified.')
        return

    # Determine if the neighbourhoods and heat sources should be refreshed
    try:
        if args[2] == 'refresh':
            # Initialise neighbourhoods and heat sources
            initialise_neighbourhoods_and_heat_sources()
    except BaseException:
        pass

    # Initialise bookkeeper to bookkeep the energy balance
    bookkeeper = Bookkeeper()

    # Load pickled (or cached) objects
    neighbourhoods = load_neighbourhoods()
    heat_sources = {'HT': load_ht_sources(), 'LT': load_lt_sources()}

    # Sort neighbourhoods on first preference percentage
    sorted_neighbourhoods = {}
    for neighbourhood in sorted(
            neighbourhoods.values(),
            key=lambda x: x.heating_option_preference[0][1],
            reverse=True):
        sorted_neighbourhoods[neighbourhood.code] = neighbourhood

    apply_decision_trees(sorted_neighbourhoods, heat_sources, bookkeeper)

    # Sort neighbourhoods on LT eligibility
    neighbourhoods = sorted_neighbourhoods
    sorted_neighbourhoods = {}
    for neighbourhood in sorted(
            neighbourhoods.values(),
            key=lambda x: x.fraction_of_lt_eligible_houses(),
            reverse=True):
        sorted_neighbourhoods[neighbourhood.code] = neighbourhood

    # Run post-analysis for all neighbourhoods (and save the refined
    # neighbourhoods into a new pickle object)
    flip_LT_eligible_neighbourhoods(bookkeeper, config.current_project.current_scenario_name, sorted_neighbourhoods, heat_sources)

    # Get future efficiency of appliances, etc.
    efficiency = config.current_project.ASSUMPTIONS['efficiency_of_appliances']
    # Add additional electricity demand (not for heating but for appliances,
    # lighting, etc.) to each neighbourhood
    for code, neighbourhood in sorted_neighbourhoods.items():
        # Calculate future electricity demands
        future_electricity_demand_residences = (neighbourhood.total_electricity_demand_of_residences() * efficiency)
        future_electricity_demand_utility = (neighbourhood.total_electricity_demand_of_utility() * efficiency)

        # Add future electricity demands to the bookkeeper
        bookkeeper.add_final_heat_demand(neighbourhood, 'E',
                                         future_electricity_demand_residences,
                                         future_electricity_demand_utility)

    # Save classified neighbourhoods (i.e., the objects with the assigned
    # heating option and source included)
    save_objects('classified_neighbourhoods', sorted_neighbourhoods)

    # Save and export bookkeeper results
    bookkeeper.save_bookkeeper()
    bookkeeper.export_heat_demand_to_csv()

    # Save assigned HT and LT sources
    save_objects('assigned_ht_sources', heat_sources['HT'])
    save_objects('assigned_lt_sources', heat_sources['LT'])

    # Run tests (let's use another script for that, separately from this one)
    run_all_tests(config.current_project.current_scenario_name)

    # Determine distance from each "W" neighbourhood to the used heat source
    determine_distance_from_neighbourhood_to_source(sorted_neighbourhoods, heat_sources)

    # Export the results to a CSV file
    export_neighbourhood_results_to_csv(sorted_neighbourhoods)
    export_heat_source_results_to_csv(heat_sources)


if __name__ == "__main__":
    main(sys.argv[1:])
