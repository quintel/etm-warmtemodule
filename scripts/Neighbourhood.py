# external modules
import numpy as np

# project modules
from classify_neighbourhoods import efficiency_of_heating_option
import config
from Matrix import Matrix
from lt_matrix import LTMatrix

WHITELIST = [
    'municipality_code', 'municipality_name', 'geo_coordinate_x',
    'geo_coordinate_y', 'adjacent_neighbourhoods', 'ht_sources_available',
    'lt_sources_available', 'space_heating_demand_per_house',
    'hot_water_demand_per_house', 'electricity_demand_per_house',
    'space_heating_demand_per_m2_utility', 'hot_water_demand_per_m2_utility',
    'electricity_demand_per_m2_utility', 'existing_heat_network_share',
    'geothermal_available', 'teo_available','number_of_historical_buildings', 'trace_length',
    'share_of_houses_demolished', 'number_of_lt_eligible_houses',
    'housing_stock_matrix', 'utility_stock_matrix', 'number_of_new_apartments',
    'number_of_new_terraced_houses', 'number_of_new_detached_houses',
    'number_of_new_semi_detached_houses', 'number_of_new_houses_unknown_type',
    'epi_of_new_houses', 'size_of_new_houses'
]


class Neighbourhood:
    """
    Class to describe a neighbourhood in terms of different properties (such as
    its building stock, coordinates, heating option preference, etc.) and
    classes (in order to determine its future heat demands, etc.)
    """

    def __init__(self, initial_values):
        self.code = initial_values['neighbourhood_code']
        self.name = initial_values['neighbourhood_name']

        self.geo_coordinate = [None, None]
        self.heating_option_preference = {}
        self.lt_elegible = False
        self.assigned_heating_option = None
        self.force_heat_network = False
        self.assigned_heat_source = None
        self.stage_of_assignment = None
        self.confidence = None
        self.share_of_houses_demolished = 0.
        self.number_of_lt_eligible_houses = 0.
        self.number_of_new_apartments = 0.
        self.number_of_new_terraced_houses = 0.
        self.number_of_new_detached_houses = 0.
        self.number_of_new_semi_detached_houses = 0.
        self.number_of_new_houses_unknown_type = 0.
        self.epi_of_new_houses = 0.
        self.size_of_new_houses = 0.
        self.trace_length = 0.


    def update(self, values):
        """
        Update the neighbourhood with additional properties
        """

        # print('\nUpdating {} {}'.format(self.code, self.name))

        for key in values:
            if key in WHITELIST:
                if key == 'geo_coordinate_x':
                    self.geo_coordinate[0] = values[key]
                elif key == 'geo_coordinate_y':
                    self.geo_coordinate[1] = values[key]
                else:
                    setattr(self, key, values[key])
            # else:
            #     print('  - {} is skipped'.format(key))


    def check_for_missing_attributes(self):
        """
        Checks if all whitelist attributes are assigned to the Neighbourhood
        """

        print('\nChecking for missing attributes in {} {}..'.format(
            self.code, self.name))

        for key in WHITELIST:
            try:
                getattr(self, key)
            except KeyError:
                print('  - {} is missing'.format(key))


    def number_of_houses(self):
        """
        Returns number of houses
        """

        number_of_houses = 0

        for type, dictionary in self.housing_stock_matrix.items():
            for year in dictionary:
                number_of_houses += dictionary[year]['aantal_woningen']

        return number_of_houses


    def m2_of_utility(self):
        """
        Returns m2 of utility
        """

        m2_of_utility = 0

        for type, dictionary in self.utility_stock_matrix.items():
            for year in dictionary:
                m2_of_utility += dictionary[year]['totaal_oppervlakte']

        return m2_of_utility


    def number_of_utility_buildings(self):
        """
        Returns number of utility buildings
        """

        number_of_utility_buildings = 0

        for type, dictionary in self.utility_stock_matrix.items():
            for year in dictionary:
                number_of_utility_buildings += dictionary[year]['aantal_gebouwen']

        return number_of_utility_buildings


    def fraction_of_lt_eligible_houses(self):
        """
        Returns the fraction of LT eligible residences
        """

        try:
            fraction = (
                self.number_of_lt_eligible_houses /
                (self.number_of_houses()) )

            return min(1., fraction)

        except ZeroDivisionError:
            return 0.


    def fraction_of_small_houses(self):
        """
        Returns the fraction of small residences (< 75 m2)
        """

        number_of_small_houses = 0

        for type, dictionary in self.housing_stock_matrix.items():
            for year in dictionary:
                number_of_small_houses += dictionary[year]['aantal_kleine_woningen']

        try:
            fraction = (
                number_of_small_houses /
                (self.number_of_houses() + self.number_of_utility_buildings()) )

            return min(1., fraction)

        except ZeroDivisionError:
            return 0.


    def fraction_of_historical_buildings(self):
        """
        Returns the fraction of historical buildings (compared to the sum of
        houses and utility buildigns)
        """

        try:
            fraction = (
                self.number_of_historical_buildings /
                (self.number_of_houses() + self.number_of_utility_buildings()))

            # For some neighbourhoods the number of historical buildings don't
            # include residences or utility buildings from the BAG. This might
            # result in a fraction higher than 1.0. If this is the case,
            # return a fraction of 1.0 instead of some value > 1.0.
            return min(1., fraction)
        except ZeroDivisionError:
            return 0.


    def linear_heat_density(self):
        """
        Returns the linear heat density (by Rik Verweij) based on the heat
        demand and the trace length.

        linear heat density = total heat demand [MWh/a] / trace length [m]
        """

        GJ_TO_MWH = config.current_project.KEY_FIGURES['gj_to_mwh']

        if self.trace_length == 0:
            return 0.
        else:
            return self.total_heat_demand() * GJ_TO_MWH / self.trace_length


    def total_electricity_demand_of_residences(self):
        """
        Returns total electricity demand of residences (for the start year)
        """

        return (self.electricity_demand_per_house * self.number_of_houses())


    def total_electricity_demand_of_utility(self):
        """
        Returns total electricity demand of utility (for the start year)
        """

        return (self.electricity_demand_per_m2_utility * self.m2_of_utility())


    def total_electricity_demand(self):
        """
        Returns total electricity demand of residences and utility (for the
        start year)
        """

        return (self.total_electricity_demand_of_residences() +
                self.total_electricity_demand_of_utility())


    def total_heat_demand(self):
        """
        Returns total useful heat demand (both for space heating and hot water)
        of residences and utility (for the start year)
        """

        return (self.total_heat_demand_of_residences() +
                self.total_heat_demand_of_utility())


    def total_heat_demand_per_house(self):
        """
        Returns total heat demand per house
        """

        return (self.space_heating_demand_per_house +
                self.hot_water_demand_per_house)


    def total_heat_demand_per_m2_utility(self):
        """
        Returns total heat demand (in GJ) per m2 utility
        """

        return (self.space_heating_demand_per_m2_utility +
                self.hot_water_demand_per_m2_utility)


    def total_space_heating_demand_of_residences(self):
        """
        Returns the total space heating demand (in GJ) for all houses
        """

        return (self.space_heating_demand_per_house) * self.number_of_houses()


    def total_hot_water_demand_of_residences(self):
        """
        Returns the total hot water demand (in GJ) for all houses
        """

        return (self.hot_water_demand_per_house) * self.number_of_houses()


    def total_space_heating_demand_of_utility(self):
        """
        Returns the total space heating demand (in GJ) for all utilities
        """

        return (
            self.space_heating_demand_per_m2_utility) * self.m2_of_utility()


    def total_hot_water_demand_of_utility(self):
        """
        Returns the total hot water demand (in GJ) for all utilities
        """

        return (self.hot_water_demand_per_m2_utility) * self.m2_of_utility()


    def total_heat_demand_of_residences(self):
        """
        Returns total heat demand (in GJ) for all houses
        """

        return (self.total_space_heating_demand_of_residences() +
                self.total_hot_water_demand_of_residences())


    def total_heat_demand_of_utility(self):
        """
        Returns total heat demand for all utilities
        """

        return (self.total_space_heating_demand_of_utility() +
                self.total_hot_water_demand_of_utility())


    def weighted_epi_of_residences(self):
        """
        Calculates the weighted (effective) EPI for all residences
        """

        weighted_epi_of_residences = 0.0

        for house_type, dictionary in self.housing_stock_matrix.items():
            for year in dictionary:
                weighted_epi_of_residences += dictionary[year][
                    'aantal_woningen'] * dictionary[year]['gem_epi']

        # Multiplying with heat and hot water demand to convert to epi * energy
        if self.number_of_houses() > 0:
            weighted_epi_of_residences /= self.number_of_houses()
        else:
            weighted_epi_of_residences = 0.0

        return weighted_epi_of_residences


    def weighted_epi_of_utility(self):
        """
        Calculates the weighted (effective) EPI for utility
        """

        weighted_epi_of_utility = 0.0

        for use_type, dictionary in self.utility_stock_matrix.items():
            for year in dictionary:
                weighted_epi_of_utility += dictionary[year][
                    'totaal_oppervlakte'] * dictionary[year]['gem_epi']

        # Multiplying with heat and hot water demand to convert to epi * energy
        if self.m2_of_utility() > 0:
            weighted_epi_of_utility /= self.m2_of_utility()
        else:
            weighted_epi_of_utility = 0.0

        return weighted_epi_of_utility


    def lookup_reduction_relative_to_current_heat_demand(
            self, building_type, weighted_epi_of_residences, desired_epi):
        """
        Looks up the reduction of the current epi with respect to label 'G'
        """

        xp, fp = zip(*config.current_project.KEY_FIGURES['epi_reduction_table'][building_type])

        current_reduction = np.interp(weighted_epi_of_residences, xp, fp)
        desired_reduction = np.interp(desired_epi, xp, fp)

        return (desired_reduction - current_reduction) / (1.0 -
                                                          current_reduction)

    def relative_heat_reduction_of_residences(self, desired_epi):
        """
        Returns the fraction of heat reduction relative to the current heat
        demand of residences based on the desired EPI. If there is a reduction,
        it must be related to the EPI by the lookup function.
        """

        weighted_epi_of_residences = self.weighted_epi_of_residences()

        if desired_epi >= weighted_epi_of_residences:
            return 0.0
        else:
            return self.lookup_reduction_relative_to_current_heat_demand(
                'residences', weighted_epi_of_residences, desired_epi)


    def relative_heat_reduction_of_utility(self, desired_epi):
        """
        Returns the fraction of heat reduction relative to the current heat
        demand of utility based on the desired EPI. If there is a reduction, it
        must be related to the EPI by the lookup function.
        """

        weighted_epi_of_utility = self.weighted_epi_of_utility()

        if desired_epi >= weighted_epi_of_utility:
            return 0.0
        else:
            return self.lookup_reduction_relative_to_current_heat_demand(
                'utility', weighted_epi_of_utility, desired_epi)


    def total_heat_demand_of_residences_after_insulation(self, heating_option):
        """
        Returns both the heat reduction and the total heat demand of residences
        after insulation measures (based on the heat reduction which follows
        from the desired EPI corresponding to the assigned heating option)
        """

        # Lookup the desired EPI for this heating option
        desired_epi = config.current_project.ASSUMPTIONS['desired_epi'][heating_option]

        # Calculate the heat reduction fraction (hot water demand does not change with insulation, only space heating demand)
        heat_reduction_fraction = self.relative_heat_reduction_of_residences(
            desired_epi)

        # Subtract heat demand reduction to calculate the space heating demand after insulation
        heat_reduction = (self.total_space_heating_demand_of_residences() *
                          heat_reduction_fraction)
        space_heating_demand_after_insulation = (
            self.total_space_heating_demand_of_residences() - heat_reduction)

        # Calculate the total heat demand after insulation (hot water demand does not change after insulation)
        total_heat_demand_after_insulation = (
            space_heating_demand_after_insulation +
            self.total_hot_water_demand_of_residences())

        return total_heat_demand_after_insulation, heat_reduction


    def total_heat_demand_of_utility_after_insulation(self, heating_option):
        """
        Returns both the heat reduction and the total heat demand of utility
        after insulation measures (based on the heat reduction which follows
        from the desired EPI corresponding to the assigned heating option)
        """

        # Lookup the desired EPI for this heating option
        desired_epi = config.current_project.ASSUMPTIONS['desired_epi'][heating_option]

        # Calculate the heat reduction (hot water demand does not change with insulation, only space heating demand)
        heat_reduction_fraction = self.relative_heat_reduction_of_utility(
            desired_epi)

        # Subtract heat demand reduction to calculate the space heating demand after insulation
        heat_reduction = (self.total_space_heating_demand_of_utility() *
                          heat_reduction_fraction)
        space_heating_demand_after_insulation = (
            self.total_space_heating_demand_of_utility() - heat_reduction)

        # Calculate the total heat demand after insulation
        total_heat_demand_after_insulation = (
            space_heating_demand_after_insulation +
            self.total_hot_water_demand_of_utility())

        return total_heat_demand_after_insulation, heat_reduction


    def total_heat_demand_after_insulation(self, heating_option):
        """
        Calculates the total heat demand of both residences and utility based
        on the heating option.
        """

        heat_demand_residences, heat_reduction_residences = self.total_heat_demand_of_residences_after_insulation(
            heating_option)
        heat_demand_utility, heat_reduction_utility = self.total_heat_demand_of_utility_after_insulation(
            heating_option)

        return ((heat_demand_residences + heat_demand_utility),
                (heat_reduction_residences + heat_reduction_utility))


    def future_heat_demand_of_residences(self,
                                         bookkeeper,
                                         heating_option):
        """
        Calculates the future heat demand of residences based on the heating
        option and heat source. The future heat demand takes the effect of
        insulation measures and efficiencies into account.
        """

        # Calculate heat demand after insulation based on the heating option
        useful_demand, heat_reduction = self.total_heat_demand_of_residences_after_insulation(heating_option)

        # Take efficiencies of heating option into account to calculate the
        # final heating demand of residences
        final_demand = (useful_demand /
                        efficiency_of_heating_option(self, heating_option))

        return final_demand, useful_demand, heat_reduction


    def future_heat_demand_of_utility(self,
                                      bookkeeper,
                                      heating_option):
        """
        Calculates the future heat demand of utility based on the heating
        option and heat source. The future heat demand takes the effect of
        insulation measures and efficiencies into account.
        """

        # Calculate heat demand after insulation based on the heating option
        useful_demand, heat_reduction = self.total_heat_demand_of_utility_after_insulation(heating_option)

        # Take efficiencies of heating option into account to calculate the
        # final heating demand of utility
        final_demand = (useful_demand /
                        efficiency_of_heating_option(self, heating_option))

        return final_demand, useful_demand, heat_reduction


    def determine_heating_option_preference(self):
        """
        Apply matrix to the neighbourhood's built environment stock
        in order to determine the first, second and third choice
        """

        # Create empty Matrix object for housing and determine the
        # heating option preference based on the housing and utility stock
        # do the same for the LTMatrix
        self.heating_option_preference = Matrix().determine_heating_option_preference(self)
        self.lt_elegible = LTMatrix().determine_heating_option_preference(self)['W_LT'] == 1
