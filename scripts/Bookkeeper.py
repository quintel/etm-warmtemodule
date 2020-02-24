# system modules
import os
import sys

# external modules
import csv
from pathlib import Path
import pickle

# project modules
import config


class Bookkeeper:
    """
    Class to hold functions for testing and bookkeeping
    """

    def __init__(self):
        """
        A dictionary is initialised to store the total heat demand per heating
        option and heat source. In addition to 'all_residences' and
        'all_utility', a key can be added for each neighbourhood to store a
        similar heat demand dictionary.

        'E': final demand electricity (GJ)
        'H': final demand renewable gas (GJ)
        'geothermal': useful demand geothermal heat (GJ)
        'HT': final demand heat from HT sources (GJ)
        'MT': final demand heat from MT sources (GJ)
        'LT': final demand heat from LT sources (GJ)
        'backup': final demand backup heat (GJ)
        'undecided': present demand (GJ)
        'useful_heat': useful demand heat for space heating and hot water (GJ)
        'heat_reduction': heat reduction by insulation (GJ)
        """

        self.heat_demand = {
            'all_residences': {
                'E': 0.,
                'H': 0.,
                'geothermal': 0.,
                'HT': 0.,
                'MT': 0.,
                'LT': 0.,
                'backup': 0.,
                'undecided': 0.,
                'useful_heat': 0.,
                'heat_reduction': 0.
            },
            'all_utility': {
                'E': 0.,
                'H': 0.,
                'geothermal': 0.,
                'HT': 0.,
                'MT': 0.,
                'LT': 0.,
                'backup': 0.,
                'undecided': 0.,
                'useful_heat': 0.,
                'heat_reduction': 0.
            }
        }


    def add_final_demand_to_neighbourhood(self, neighbourhood, heat_type,
                                          final_heat_demand_residences,
                                          final_heat_demand_utility):
        """
        Add final heat demand for all residences and utility in the neighbourhood
        """

        # Initialise neighbourhood object
        if not neighbourhood.code in self.heat_demand.keys():
            self.heat_demand[neighbourhood.code] = {
                'residences': {},
                'utility': {}
            }

        # Add heat demand
        try:
            self.heat_demand[neighbourhood.code]['residences'][
                heat_type] += final_heat_demand_residences
            self.heat_demand[neighbourhood.code]['utility'][
                heat_type] += final_heat_demand_utility
        except KeyError:
            self.heat_demand[neighbourhood.code]['residences'][
                heat_type] = final_heat_demand_residences
            self.heat_demand[neighbourhood.code]['utility'][
                heat_type] = final_heat_demand_utility


    def add_useful_demand_to_neighbourhood(self, neighbourhood,
                                           useful_heat_demand_residences,
                                           useful_heat_demand_utility,
                                           heat_reduction_residences,
                                           heat_reduction_utility):
        """
        Add useful heat demand and heat reduction for all residences and utility in the neighbourhood
        """

        # Initialise neighbourhood object if it doesn't exist yet
        if not neighbourhood.code in self.heat_demand.keys():
            self.heat_demand[neighbourhood.code] = {
                'residences': {},
                'utility': {}
            }

        # Add heat demand
        try:
            self.heat_demand[neighbourhood.code]['residences'][
                'useful_heat'] += useful_heat_demand_residences
            self.heat_demand[neighbourhood.code]['residences'][
                'heat_reduction'] += heat_reduction_residences
            self.heat_demand[neighbourhood.code]['utility'][
                'useful_heat'] += useful_heat_demand_utility
            self.heat_demand[neighbourhood.code]['utility'][
                'heat_reduction'] += heat_reduction_utility
        except KeyError:
            self.heat_demand[neighbourhood.code]['residences'][
                'useful_heat'] = useful_heat_demand_residences
            self.heat_demand[neighbourhood.code]['residences'][
                'heat_reduction'] = heat_reduction_residences
            self.heat_demand[neighbourhood.code]['utility'][
                'useful_heat'] = useful_heat_demand_utility
            self.heat_demand[neighbourhood.code]['utility'][
                'heat_reduction'] = heat_reduction_utility


    def add_final_heat_demand(self, neighbourhood, heat_type,
                              final_heat_demand_residences,
                              final_heat_demand_utility):
        """
        The argument heat_type can represent the following types:

        'E': electricity (heating_option 'E')
        'H': renewable gas (heating_option 'H')
        'geothermal': heat from a geothermal source (heating_option 'W')
        'HT': heat from an HT source (heating_option 'W')
        'MT': heat from an MT source (heating_option 'W')
        'LT': heat from an LT source (heating_option 'W' or 'E')
        'backup': heat from a backup source (heating_option 'W' or 'H')
        """

        # Add final heat demand for all residences in the total region
        self.heat_demand['all_residences'][
            heat_type] += final_heat_demand_residences

        # Add final heat demand for all utility in the total region
        self.heat_demand['all_utility'][heat_type] += final_heat_demand_utility

        # Add final heat demand for all residences and utilities in the neighbourhood
        self.add_final_demand_to_neighbourhood(neighbourhood, heat_type,
                                               final_heat_demand_residences,
                                               final_heat_demand_utility)


    def add_useful_heat_demand(self, neighbourhood,
                               useful_heat_demand_residences,
                               useful_heat_demand_utility,
                               heat_reduction_residences,
                               heat_reduction_utility):
        """
        Description
        """

        # Add useful heat demand and reduction for all residences in the total region
        self.heat_demand['all_residences'][
            'useful_heat'] += useful_heat_demand_residences
        self.heat_demand['all_residences'][
            'heat_reduction'] += heat_reduction_residences

        # Add useful heat demand and reduction for all utility in the total region
        self.heat_demand['all_utility'][
            'useful_heat'] += useful_heat_demand_utility
        self.heat_demand['all_utility'][
            'heat_reduction'] += heat_reduction_utility

        # Add final heat demand for all residences and utilities in the neighbourhood
        self.add_useful_demand_to_neighbourhood(neighbourhood,
                                                useful_heat_demand_residences,
                                                useful_heat_demand_utility,
                                                heat_reduction_residences,
                                                heat_reduction_utility)

        # TODO: Is this the best place to store the neighbourhood specific heat
        # demand data? Or would it be better to store this in the Neighbourhood
        # object itself?


    def print_heat_demand(self):

        print("\nFinal demands for residences:")
        for key, value in self.heat_demand['all_residences'].items():
            print('  {}: {} PJ'.format(key, value / 1.E6))

        print("\nFinal demands for utility:")
        for key, value in self.heat_demand['all_utility'].items():
            print('  {}: {} PJ'.format(key, value / 1.E6))

        print("\nTotal useful heat demand: {} PJ".format(
            (self.heat_demand['all_utility']['useful_heat'] +
             self.heat_demand['all_residences']['useful_heat']) / 1.E6))

        print("Total heat reduction: {} PJ".format(
            (self.heat_demand['all_utility']['heat_reduction'] +
             self.heat_demand['all_residences']['heat_reduction']) / 1.E6))

        print("Total useful demand + heat reduction: {} PJ".format(
            ((self.heat_demand['all_utility']['useful_heat'] +
              self.heat_demand['all_residences']['useful_heat']) / 1.E6) +
            (self.heat_demand['all_utility']['heat_reduction'] +
             self.heat_demand['all_residences']['heat_reduction']) / 1.E6))


    def export_heat_demand_to_csv(self, name_extension=""):
        """
        Export heat demand to CSV file
        """

        path = Path(
            __file__).resolve().parents[1] / "output_data" / "{}".format(
                config.current_project_name) / "{}".format(
                config.current_project.current_scenario_name) / "demands.csv".format(name_extension)

        # Define the columns variable
        columns = [
            'neighbourhood', 'type', 'E', 'H', 'geothermal', 'HT', 'MT', 'LT',
            'backup', 'undecided', 'useful_heat', 'heat_reduction'
        ]

        # Write the neighbourhood objects to csv file rows
        with open(path, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for object in self.heat_demand:
                if object == 'all_residences':
                    characteristics = {
                        'neighbourhood': 'total',
                        'type': 'residences'
                    }
                    writer.writerow({
                        **characteristics,
                        **self.heat_demand[object]
                    })
                elif object == 'all_utility':
                    characteristics = {
                        'neighbourhood': 'total',
                        'type': 'utility'
                    }
                    writer.writerow({
                        **characteristics,
                        **self.heat_demand[object]
                    })
                else:
                    for type in ['residences', 'utility']:
                        characteristics = {
                            'neighbourhood': object,
                            'type': type
                        }
                        writer.writerow({
                            **characteristics,
                            **self.heat_demand[object][type]
                        })

        print("Sucessfully wrote heat demand to CSV file!")


    def save_bookkeeper(self, name_extension=""):
        """
        Save bookkeeper to pickle file
        """

        # Writing future heat demands to CSV file
        path = Path(
            __file__).resolve().parents[1] / "output_data" / "{}".format(
                config.current_project_name) / "{}".format(
                config.current_project.current_scenario_name) / "bookkeeper{}.pkl".format(name_extension)

        # Create file/folders if non-existent
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Write to pickle
        with open(path, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

        print(
            "\nSucessfully wrote bookkeeper object to pickle file for testing!"
        )


    def load_bookkeeper(self):
        """
        Load bookkeeper object from pickle file
        """

        # Load pickled heat demands object (cached data)
        path = Path(
            __file__).resolve().parents[1] / "output_data" / "{}".format(
                config.current_project_name) / "{}".format(
                config.current_project.current_scenario_name) / "bookkeeper.pkl"

        with open(path, 'rb') as input:
            bookkeeper = pickle.load(input)

        return bookkeeper
