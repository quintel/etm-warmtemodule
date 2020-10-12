# external modules
import math
import numpy as np

# project modules
import config


class Matrix:
    """
    Class to describe the heating option preference for each cell of the matrix
    """

    def __init__(self, number_of_options=3):
        self.residences_matrix = config.current_project.DEFAULT_MATRIX_RESIDENCES
        self.utility_matrix = config.current_project.DEFAULT_MATRIX_UTILITY

        # Vectors represent [E, W, H] by default
        self.heat_demand_vector = np.zeros(number_of_options)
        self.heat_demand_vector_residences = np.zeros(number_of_options)
        self.heat_demand_vector_utility = np.zeros(number_of_options+1)
        self.normalized_vector = np.zeros(number_of_options)


    def determine_heating_option_preference(self, neighbourhood):
        """
        Determine the neighbourhood's heating option preference by:
        1) Applying the default matrix to the housing and utility stock
        2) Normalizing the heating option preference vector to values in [0,1]
        3) Taking the linear heat density offset into account
        4) Sorting the heating option preference vector by preference
        """

        # Determine heating option vector based on housing stock
        self.apply_matrix_to_housing_stock(neighbourhood)

        # Determine heating option vector based on utility stock
        self.apply_matrix_to_utility_stock(neighbourhood)

        # Determine combined heating option vector based on both housing and
        # utility stock
        self.heat_demand_vector = (self.heat_demand_vector_residences +
                                   self.heat_demand_vector_utility)

        # Normalize combined heating option vector
        if np.sum(self.heat_demand_vector) > 0.:
            self.normalized_vector = self.heat_demand_vector / np.sum(
                self.heat_demand_vector)

        return self.sorted_preference(neighbourhood)

    def sorted_preference(self, neighbourhood):
        '''
        Returns the sorted peference for the given neighbourhood
        '''

        # Take linear heat density offset into account
        offset = self.determine_linear_heat_density_offset(neighbourhood)

        # Cast normalized vector to heating options
        heating_option_preference = {
            'W_MTHT': offset + (1. - offset) * self.normalized_vector[0],
            'H': (1. - offset) * self.normalized_vector[1],
            'E': (1. - offset) * self.normalized_vector[2]
        }

        # Sort by value to determine the neighbourhood's preferences
        return sorted(heating_option_preference.items(),
                      key=lambda x: x[1],
                      reverse=True)


    def apply_matrix_to_housing_stock(self, neighbourhood):
        """
        Apply the residences matrix to the neighbourhood's housing stock:

        For each cell in the matrix:
        1) Multiply each vector by the total heat demand
        2) Add the product to the sum of all vectors

        Then, check if the sum of the vector is equal to the total heat demand
        of the neighbourhood's residences.
        """

        # For each cell in matrix,
        for housing_type, dictionary in self.residences_matrix.items():
            for year_class in dictionary:
                total_heat_demand = 0.

                if year_class in neighbourhood.housing_stock_matrix[housing_type].keys():
                    number_of_houses = neighbourhood.housing_stock_matrix[housing_type][year_class]['aantal_woningen']

                    # multiply each vector by the total heat demand,
                    total_heat_demand = (
                        number_of_houses *
                        neighbourhood.total_heat_demand_per_house())

                # and add product to the sum of all vectors
                self.heat_demand_vector_residences += (
                    np.array(self.residences_matrix[housing_type][year_class]) *
                    total_heat_demand)

        # Check if the sum of the vector is equal to the total heat demand of
        # the neighbourhood's residences. If not, warn the user.
        if not math.isclose(np.sum(self.heat_demand_vector_residences),
                            neighbourhood.total_heat_demand_of_residences()):
            print(
                '\nWARNING! For {}, the sum of the heating option vector for residences is not equal to the total heat demand ({} != {})'
                .format(neighbourhood.code,
                        np.sum(self.heat_demand_vector_residences),
                        neighbourhood.total_heat_demand_of_residences()))


    def apply_matrix_to_utility_stock(self, neighbourhood):
        """
        Apply the utility matrix to the neighbourhood's utility stock:

        For each cell in the matrix:
        1) Multiply each vector by the total heat demand
        2) Add the product to the sum of all vectors

        Then, check if the sum of the vector is equal to the total heat demand
        of the neighbourhood's residences.
        """

        # For each cell in matrix,
        for building_type, dictionary in self.utility_matrix.items():
            for size_class in dictionary:
                total_heat_demand = 0.

                if size_class in neighbourhood.utility_stock_matrix[building_type].keys():
                    m2_of_utility = neighbourhood.utility_stock_matrix[building_type][size_class]['totaal_oppervlakte']

                    # multiply each vector by the total heat demand
                    total_heat_demand = (
                        m2_of_utility *
                        neighbourhood.total_heat_demand_per_m2_utility())

                # and add product to the sum of all vectors
                self.heat_demand_vector_utility += np.array(self.utility_matrix[building_type][size_class]) * total_heat_demand

        # The last entry of the utility vector contains the m2 of utility that
        # 'follows' residences. Here, the residences vector is multiplied by
        # that share of the total heat demand of utilities and added to the
        # utilities vector which is now also a length-3 vector
        if self.heat_demand_vector_utility[-1] > 0.:
            if np.sum(self.heat_demand_vector_residences) > 0.:
                normalized_vector_residences = self.heat_demand_vector_residences / np.sum(self.heat_demand_vector_residences)
                self.heat_demand_vector_utility = self.heat_demand_vector_utility[:-1] + self.heat_demand_vector_utility[-1] * normalized_vector_residences

            elif np.sum(self.heat_demand_vector_utility[:-1]) > 0.:
                # If residential vector is empty, add utility vector (except last entry) to itself
                normalized_vector_utility = self.heat_demand_vector_utility[:-1] / np.sum(self.heat_demand_vector_utility[:-1])
                self.heat_demand_vector_utility = self.heat_demand_vector_utility[:-1] + self.heat_demand_vector_utility[-1] * normalized_vector_utility

            else:
                self.heat_demand_vector_utility = np.zeros(len(self.heat_demand_vector_residences))

        else:
            self.heat_demand_vector_utility = self.heat_demand_vector_utility[:-1]

        # Check if the sum of the vector is equal to the total heat demand of
        # the neighbourhood's utilities. If not, warn the user.
        if not math.isclose(np.sum(self.heat_demand_vector_utility),
                            neighbourhood.total_heat_demand_of_utility()):
            if np.sum(self.heat_demand_vector_utility) > 0.:
                print(
                    '\nWARNING! For {}, the sum of the heating option vector for utility is not equal to the total heat demand ({} != {})'
                    .format(neighbourhood.code,
                            np.sum(self.heat_demand_vector_utility),
                            neighbourhood.total_heat_demand_of_utility()))


    def determine_linear_heat_density_offset(self, neighbourhood):
        """
        Take linear heat density (by Rik Verweij) into account; use it as an
        offset for the residences and utility matrix
        """

        # Get the maximal offset possible set in the config.current_project.file
        max_offset = config.current_project.ASSUMPTIONS['linear_heat_density_max_offset']

        # Initialise the offset for the neighbourhood
        offset = 0.

        # Calculate the neighbourhood's linear heat density
        linear_heat_density = neighbourhood.linear_heat_density()

        # If linear heat density < 1, there is no offset
        if linear_heat_density < 1.:
            offset = 0.
        # Else if 1 <= linear heat density <= 2, calculate the offset
        elif linear_heat_density <= 2.:
            offset = max_offset * (linear_heat_density - 1.)
        # Else if linear heat density > 2, use the max offset
        elif linear_heat_density > 2.:
            offset = max_offset

        return offset
