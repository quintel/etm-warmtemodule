"""
TO DO:

*) Methods for slider configuration ETM?

*) Write tests or consistency checks for
     - useful demand for households and utility
     - final demand for the carriers for space heating + hot water for
       households and utility
"""

# system modules
import os
import sys

# external modules
import math
from pathlib import Path
import pickle

# project modules
import config


def load_classified_neighbourhoods():
    """
    Load classified neighbourhoods from pickle
    """

    # Load pickled neighbourhood objects (cached data)
    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "classified_neighbourhoods.pkl")

    with open(path, 'rb') as input:
        neighbourhoods = pickle.load(input)

    return neighbourhoods


def load_bookkeeper():
    """
    Load bookkeeper from pickle
    """

    # Load pickled bookkeeper object (cached data)
    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "bookkeeper.pkl")

    with open(path, 'rb') as input:
        bookkeeper = pickle.load(input)

    return bookkeeper


def load_ht_sources():
    """
    Load pickled HT source objects (cached data)
    """

    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "assigned_ht_sources.pkl")

    with open(path, 'rb') as input:
        ht_sources = pickle.load(input)

    return ht_sources


def load_lt_sources():
    """
    Load pickled LT source objects (cached data)
    """

    path = (Path(__file__).resolve().parents[1] / "output_data" /
            f"{config.current_project_name}" /
            f"{config.current_project.current_scenario_name}" /
            "assigned_lt_sources.pkl")

    with open(path, 'rb') as input:
        lt_sources = pickle.load(input)

    return lt_sources


def check_equality(name1, value1, name2, value2):
    """
    Description
    """

    if math.isclose(value1, value2):
        print('  CORRECT: {} ({}) == {} ({})'.format(name1, round(value1, 1),
                                                     name2, round(value2, 1)))
        return
    else:
        print('  ERROR: {} ({}) != {} ({}) => difference: {}'.format(
            name1, round(value1, 1), name2, round(value2, 1),
            abs(round(value1 - value2, 1))))


def present_useful_heat_demand(neighbourhoods):
    """
    Calculates the total present useful heat demand for all neighbourhoods
    """

    present_useful_heat_demand = 0.
    for neighbourhood in neighbourhoods.values():
        present_useful_heat_demand += neighbourhood.total_heat_demand()

    return present_useful_heat_demand


def future_useful_heat_demand(neighbourhoods):
    """
    Calculates the total present useful heat demand for all neighbourhoods
    """

    future_useful_heat_demand = 0.
    future_heat_reduction = 0.

    for neighbourhood in neighbourhoods.values():
        if neighbourhood.assigned_heating_option == 'undecided':
            future_useful_heat_demand += neighbourhood.total_heat_demand()
            future_heat_reduction += 0.

        else:
            heat_demand, heat_reduction = neighbourhood.total_heat_demand_after_insulation(
                neighbourhood.assigned_heating_option)

            future_useful_heat_demand += heat_demand
            future_heat_reduction += heat_reduction

    return future_useful_heat_demand, future_heat_reduction


def future_useful_heat_demand_by_bookkeeper(bookkeeper):
    """
    Gets the bookkeeped total future useful heat demand and heat reduction for
    all neighbourhoods
    """

    useful_heat_demand = 0.
    heat_reduction = 0.

    for type in ['all_residences', 'all_utility']:
        useful_heat_demand += bookkeeper.heat_demand[type]['useful_heat']
        heat_reduction += bookkeeper.heat_demand[type]['heat_reduction']

    return useful_heat_demand, heat_reduction


def run_all_tests(scenario):
    """
    Run all tests
    """

    # Set scenario
    config.current_project.set_current_scenario(scenario)

    # Load pickled (or cached) objects
    neighbourhoods = load_classified_neighbourhoods()
    bookkeeper = load_bookkeeper()
    heat_sources = {'HT': load_ht_sources(), 'LT': load_lt_sources()}

    number_of_houses = 0
    m2_of_utility = 0
    for neighbourhood in neighbourhoods.values():
        number_of_houses += neighbourhood.number_of_houses()
        m2_of_utility += neighbourhood.m2_of_utility()

    print('\n# houses: {}'.format(number_of_houses))
    print('m2 of utility: {}'.format(m2_of_utility))

    # Print Bookkeeper demands
    bookkeeper.print_heat_demand()

    # Calculate heat demands of neighbourhood objects
    useful_heat_demand_present = present_useful_heat_demand(neighbourhoods)
    heat_demands = future_useful_heat_demand(neighbourhoods)
    useful_heat_demand_future = heat_demands[0]
    heat_reduction_future = heat_demands[1]

    # Calculate bookkeeped heat demands
    bookkeeped_heat_demands = future_useful_heat_demand_by_bookkeeper(
        bookkeeper)
    bookkeeped_useful_heat_demand_future = bookkeeped_heat_demands[0]
    bookkeeped_heat_reduction_future = bookkeeped_heat_demands[1]

    print('\nChecking total demands..')
    # Check if the present useful heat demand is equal to the sum of the future
    # useful heat demand and the heat reduction?
    check_equality('present useful heat demand', useful_heat_demand_present,
                   'future useful heat demand + heat reduction',
                   (useful_heat_demand_future + heat_reduction_future))

    # Check if the present useful heat demand (sum of all neighbourhoods) is
    # equal to the bookkeeped sum of the future useful heat demand and the
    # future heat reduction?
    check_equality('present useful heat demand', useful_heat_demand_present,
                   'bookkeeped future useful heat demand + heat reduction',
                   (bookkeeped_useful_heat_demand_future +
                    bookkeeped_heat_reduction_future))

    # Check per heat source if used heat < budget ?
    for heat_temperature in ['HT', 'LT']:
        print('\nChecking {} sources..'.format(heat_temperature))

        total_available_heat = 0.
        total_assigned_heat = 0.

        for source in heat_sources[heat_temperature].values():
            total_available_heat += source.available_heat
            total_assigned_heat += source.used_heat

            if source.used_heat <= source.available_heat:
                # print('  CORRECT: {} used heat ({}) <= available heat ({})'.format(source.code, source.used_heat, source.available_heat))
                continue
            else:
                print(
                    '  ERROR: {} used heat ({}) > available heat ({})'.format(
                        source.code, source.used_heat, source.available_heat))

        # Check if all sources (in total) haven't assigned more heat than is available
        if total_assigned_heat <= total_available_heat:
            print(
                '  CORRECT: total assigned heat ({}) <= total available heat ({})'
                .format(round(total_assigned_heat, 1),
                        round(total_available_heat, 1)))
        else:
            print(
                '  ERROR: total assigned heat ({}) > total available heat ({})'
                .format(round(total_assigned_heat, 1),
                        round(total_available_heat, 1)))

        # Check if all heat assigned by heat sources sums to the received heat by neighbourhoods
        total_used_heat = (
            bookkeeper.heat_demand['all_residences'][heat_temperature] +
            bookkeeper.heat_demand['all_utility'][heat_temperature])
        check_equality('total assigned heat', total_assigned_heat,
                       'total used heat', total_used_heat)

    # Check gas budgets
    print('\nChecking gas budgets..')

    total_available_gas = config.current_project.current_scenario['renewable_gas_budget']
    total_assigned_gas = config.current_project.current_scenario['used_renewable_gas']
    total_used_gas = bookkeeper.heat_demand['all_residences'][
        'H'] + bookkeeper.heat_demand['all_utility']['H']

    # Check if no more gas has been assigned than available
    if total_assigned_gas <= total_available_gas:
        print('  CORRECT: total assigned gas ({}) <= total available gas ({})'.
              format(round(total_assigned_gas, 1),
                     round(total_available_gas, 1)))
    else:
        print('  ERROR: total assigned gas ({}) > total available gas ({})'.
              format(round(total_assigned_gas, 1),
                     round(total_available_gas, 1)))

    # Check if all gas assigned is equal to the received gas by neighbourhoods
    check_equality('total assigned gas', total_assigned_gas, 'total used gas',
                   total_used_gas)


if __name__ == '__main__':
    run_all_tests('scenario_1')
