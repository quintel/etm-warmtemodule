# system modules
import os
import sys

# external modules
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
from scipy.spatial import Delaunay

# project modules
from Bookkeeper import Bookkeeper
from classify_neighbourhoods import (add_electricity_demand_to_bookkeeper,
                                     heat_sources_available)
import config


def correct_bookkeeper_demands(neighbourhood, bookkeeper):
    """
    Correct the neighbourhood's demands in the bookkeeper if the heating option
    was switched from the former option to an LT heat network.
    """

    # Calculate final heat demand for residences
    final_heat_demand_residences, useful_heat_demand_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
        bookkeeper, 'E')

    # Calculate final heat demand for utility
    final_heat_demand_utility, useful_heat_demand_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
        bookkeeper, 'E')

    # Add useful demands to the bookkeeper
    bookkeeper.add_useful_heat_demand(neighbourhood,
                                      -useful_heat_demand_residences,
                                      -useful_heat_demand_utility,
                                      -heat_reduction_residences,
                                      -heat_reduction_utility)

    # Add final demands to the bookkeeper
    bookkeeper.add_final_heat_demand(neighbourhood, 'E',
                                     -final_heat_demand_residences,
                                     -final_heat_demand_utility)


def flip_LT_eligible_neighbourhoods(bookkeeper, scenario, neighbourhoods, heat_sources):
    """
    If a neighbourhood's LT eligibility exceeds the threshold--i.e., it has a
    significant share of relatively new, "dense" houses--the assigned heating
    option may be flipped to a LT heat network, given that there is (still) an
    LT heat source available for this neighbourhood.
    """

    number_of_flipped_neighbourhoods = 0

    # Set scenario
    config.current_project.set_current_scenario(scenario)

    for code, neighbourhood in neighbourhoods.items():
        # Check if the neighbourhood's heating option is 'E' and if the
        # neighbourhood is eligible for LT
        if ((neighbourhood.assigned_heating_option == 'E') and
            (neighbourhood.fraction_of_lt_eligible_houses() >= config.current_project.ASSUMPTIONS['lt_eligibility'])):
            # Check if there is a LT source in range available
            if heat_sources_available(neighbourhood, 'W', heat_sources['LT'],
                                      'LT', bookkeeper):
                # Replace former heating option by 'W'
                neighbourhood.assigned_heating_option = 'W'

                # Correct energy demands in bookkeeper
                correct_bookkeeper_demands(neighbourhood, bookkeeper)

                # Update the confidence based on the corresponding heating option preference
                # neighbourhood.confidence = ...

                # Assign post-analysis as stage of assignment
                neighbourhood.stage_of_assignment = 'post-analysis'

                # Increment number of flipped neighbourhoods
                number_of_flipped_neighbourhoods += 1

    print("\nPOST-ANALYSIS: {} neighbourhoods have been flipped to W-LT".format(number_of_flipped_neighbourhoods))


if __name__ == '__main__':
    bookkeeper = Bookkeeper()
    post_analysis(bookkeeper, 'scenario_1')
