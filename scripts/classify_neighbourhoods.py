# external modules
import numpy as np

# project modules
import config


def apply_pre_analysis(neighbourhood, heat_sources, bookkeeper):
    """
    Applies pre-analysis to the neighbourhood. A check is performed if the
    neighbourhood has a heating option preference. If not (i.e., there is
    insufficient data available or there are no houses), "undecided" is
    assigned as the heating option (with confidence = 0).
    """

    # Does the neighbourhood have a heating option preference?
    # If not, assign heating option 'undecided'
    if sum(n for _, n in neighbourhood.heating_option_preference) == 0.:
        neighbourhood.assigned_heating_option = 'undecided'

        # Add present heat demand to bookkeeper
        add_present_heat_demand_to_bookkeeper(neighbourhood, bookkeeper)


def apply_electricity_decision_tree(neighbourhood, heat_sources,
                                    is_second_time, bookkeeper):
    """
    Apply electricity decision tree: if the neighbourhood's heating preference
    is all-electric, assign this option. Also check for W_LT
    """

    # Check if this is either second time, or the neighbourhood does not want a W_LT
    if is_second_time or not neighbourhood.lt_elegible:
        neighbourhood.assigned_heating_option = 'E'
        neighbourhood.assigned_heat_source = None
        add_electricity_demand_to_bookkeeper(neighbourhood, bookkeeper)
        return

    # Else check for W_LT
    if heat_sources_available(neighbourhood, 'W_LT', heat_sources['LT'], 'LT', bookkeeper):
        neighbourhood.assigned_heating_option = 'W_LT'
        return

    if teo_available(neighbourhood, bookkeeper):
        neighbourhood.assigned_heating_option = 'W_LT'
        return

    neighbourhood.assigned_heating_option = 'E'
    neighbourhood.assigned_heat_source = None
    add_electricity_demand_to_bookkeeper(neighbourhood, bookkeeper)


def apply_heat_decision_tree(neighbourhood, heat_sources, is_pre_analysis,
                             is_second_time, bookkeeper):
    """
    Apply heat decision tree: if the neighbourhood's heating preference is
    heat network, check if there are (still) heat sources available with
    sufficient remaining heat to meet the neighbourhood's demand.
    """

    # Hypothetically assign 'W_MTHT' to the neighbourhood. If W doesn't work out,
    # the heating option will be assigned to None again.
    neighbourhood.assigned_heating_option = 'W_MTHT'

    # If there is an HT source available for this neighbourhood, assign it
    # (otherwise keep None)
    if heat_sources_available(neighbourhood, 'W_MTHT', heat_sources['HT'], 'HT',
                              bookkeeper):

        return

    # Else if there is a geothermal source available for this neighbourhood,
    elif geothermal_available(neighbourhood, bookkeeper):

        return

    # Else if there is an LT source available,
    elif heat_sources_available(neighbourhood, 'W_MTHT', heat_sources['LT'], 'LT',
                                bookkeeper):

        return

    # Else if the decision tree is applied in the pre-analysis,
    # and no suitable option can be found, assign 'W_MTHT' and
    # use the gas budgets as a backup heat source
    elif is_pre_analysis:
        if gas_available(neighbourhood, 'W_MTHT', bookkeeper, 'backup'):
            neighbourhood.assigned_heat_source = 'backup'

            return

    # Else if the decision tree is applied for the second time,
    # and no suitable option can be found, assign 'E'
    elif is_second_time:
        neighbourhood.assigned_heating_option = 'E'

        # Add heat demand to bookkeeper
        add_electricity_demand_to_bookkeeper(neighbourhood, bookkeeper)

        return

    # If the decision tree is applied for the first time,
    # and no suitable option can be found, assign None (or 'undecided')
    else:
        neighbourhood.assigned_heating_option = None

        return


def apply_hybrid_decision_tree(neighbourhood, heat_sources, is_second_time,
                               bookkeeper):
    """
    Apply hybrid decision tree: if the neighbourhood's heating preference is
    hybrid or renewable gas, check if there is (still) sufficient gas left to
    meet the neighbourhood's demand.
    """

    heating_option = None

    # If there is network gas available for this neighbourhood,
    # assign 'H'
    if gas_available(neighbourhood, 'H', bookkeeper, 'H'):
        heating_option = 'H'

    # Else if the decision tree is applied for the second time,
    # and no suitable option can be found, assign 'E'
    elif is_second_time:
        heating_option = 'E'

        # Add heat demand to bookkeeper
        add_electricity_demand_to_bookkeeper(neighbourhood, bookkeeper)

    # If no suitable option can be found for this neighbourhood,
    # return None, representing 'undecided'
    neighbourhood.assigned_heating_option = heating_option


def sort_heat_sources_for_neighbourhood(neighbourhood, heat_sources,
                                        heat_temperature):
    """
    Sort heat sources for neighbourhood by distance to the neighbourhood
    """

    # Available heat sources for the neighbourhood
    if heat_temperature == 'HT':
        available_heat_sources = neighbourhood.ht_sources_available
    elif heat_temperature == 'LT':
        available_heat_sources = neighbourhood.lt_sources_available

    # Create array to store heat sources sorted by its distance to the
    # neighbourhood
    sorted_heat_sources = []

    # Split string into array with all available HT sources
    for heat_source_code in available_heat_sources:
        # Lookup heat source by code
        heat_source = heat_sources[heat_source_code]

        # Check distance to heat source
        distance_to_heat_source = np.linalg.norm(
            np.array(neighbourhood.geo_coordinate) -
            np.array(heat_source.geo_coordinate))

        # Add heat source to array
        sorted_heat_sources.append({
            'source': heat_source,
            'distance': distance_to_heat_source
        })

    # Return sorted heat sources by distance
    return sorted(sorted_heat_sources, key=lambda x: x['distance'])


def heat_sources_available(neighbourhood, heating_option, heat_sources,
                           heat_temperature, bookkeeper):
    """
    Check if there is a heat source available for the neighbourhood
    """

    # Calculate future heat demand for residences
    final_heat_demand_residences, useful_heat_demand_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
        bookkeeper, heating_option)

    # Calculate future heat demand for utility
    final_heat_demand_utility, useful_heat_demand_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
        bookkeeper, heating_option)

    # Get efficiency of using residual heat for the heat network
    try:
        share_of_residual_heat = config.current_project.SPECS[
            'share_of_{}_heat'.format(heat_temperature)
        ]
    except KeyError:
        share_of_residual_heat = config.current_project.SPECS[
            f'share_of_{heat_temperature}_heat_for_{heating_option}'
        ]

    # Calculate final demand of residual heat
    final_residual_heat_demand_residences = (final_heat_demand_residences * share_of_residual_heat)
    final_residual_heat_demand_utility = (final_heat_demand_utility * share_of_residual_heat)

    # Calculate final demand of backup heat for cofiring
    final_backup_demand_residences = final_heat_demand_residences * (
        1. - share_of_residual_heat)
    final_backup_demand_utility = final_heat_demand_utility * (
        1. - share_of_residual_heat)

    # Calculate future heat demand for the two combined
    final_residual_heat_demand = (final_residual_heat_demand_residences +
                                  final_residual_heat_demand_utility)

    # Sort heat sources by distance for the neighbourhood
    available_sources = sort_heat_sources_for_neighbourhood(
        neighbourhood, heat_sources, heat_temperature)

    # print('   Checking for available {} sources..'.format(heat_temperature))
    for available_source in available_sources:
        # Check if closest heat source has heat left for this neighbourhood
        available_source_object = heat_sources[available_source['source'].code]
        remaining_heat = (available_source_object.available_heat -
                          available_source_object.used_heat)

        if remaining_heat > final_residual_heat_demand:
            assigned_source = available_source_object.code

            # If so, assign heat source to neighbourhood and increase used heat
            neighbourhood.assigned_heat_source = assigned_source
            available_source_object.used_heat += final_residual_heat_demand

            # Add future heat demands to the bookkeeper
            bookkeeper.add_useful_heat_demand(neighbourhood,
                                              useful_heat_demand_residences,
                                              useful_heat_demand_utility,
                                              heat_reduction_residences,
                                              heat_reduction_utility)

            # Add final demands to the bookkeeper
            bookkeeper.add_final_heat_demand(neighbourhood, heat_temperature,
                                             useful_heat_demand_residences,
                                             useful_heat_demand_utility)
            bookkeeper.add_final_heat_demand(neighbourhood, 'backup',
                                             final_backup_demand_residences,
                                             final_backup_demand_utility)

            return True

    # If there is no residual heat source available, return False
    return False


def geothermal_available(neighbourhood, bookkeeper):
    """
    Check if there's geothermal heat available for the neighbourhood
    """

    # If there is a geothermal source available for this neighbourhood,
    if neighbourhood.geothermal_available:
        # Assign this source
        neighbourhood.assigned_heat_source = 'geothermal'

        # Calculate future heat demand for residences
        final_heat_demand_residences, useful_heat_demand_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
            bookkeeper, 'W_MTHT')

        # Calculate future heat demand for utility
        final_heat_demand_utility, useful_heat_demand_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
            bookkeeper, 'W_MTHT')

        # Add future heat demands to the bookkeeper
        bookkeeper.add_useful_heat_demand(neighbourhood,
                                          useful_heat_demand_residences,
                                          useful_heat_demand_utility,
                                          heat_reduction_residences,
                                          heat_reduction_utility)

        # Get share of using geothermal heat for the heat network
        share_of_geothermal_heat = config.current_project.SPECS[
            'share_of_geothermal_heat']

        # Calculate final demand of geothermal heat
        final_geothermal_demand_residences = (final_heat_demand_residences * share_of_geothermal_heat)
        final_geothermal_demand_utility = (final_heat_demand_utility * share_of_geothermal_heat)

        # Calculate final demand of backup heat for cofiring
        final_backup_demand_residences = final_heat_demand_residences * (
            1. - share_of_geothermal_heat)
        final_backup_demand_utility = final_heat_demand_utility * (
            1. - share_of_geothermal_heat)

        # Add final demands to the bookkeeper
        bookkeeper.add_final_heat_demand(neighbourhood, 'geothermal',
                                         useful_heat_demand_residences,
                                         useful_heat_demand_utility)
        bookkeeper.add_final_heat_demand(neighbourhood, 'backup',
                                         final_backup_demand_residences,
                                         final_backup_demand_utility)

        return True

    # If there is no geothermal source available, return False
    return False

def teo_available(neighbourhood, bookkeeper):
    """
    Check if there's TEO heat available for the neighbourhood
    """

    # If there is a teo source available for this neighbourhood,
    if not neighbourhood.teo_available:
        return False

    # Assign this source
    neighbourhood.assigned_heat_source = 'TEO'

    # Calculate future heat demand for residences and utility
    final_hd_residences, useful_hd_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
        bookkeeper, 'W_LT')

    final_hd_utility, useful_hd_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
        bookkeeper, 'W_LT')

    # Add future heat demands to the bookkeeper
    bookkeeper.add_useful_heat_demand(neighbourhood,
                                      useful_hd_residences,
                                      useful_hd_utility,
                                      heat_reduction_residences,
                                      heat_reduction_utility)

    # Get share of using TEO heat for the heat network
    share_of_teo_heat = config.current_project.SPECS['share_of_teo_heat']

    # Calculate final demand of backup heat for cofiring
    final_backup_demand_residences = final_hd_residences * (1. - share_of_teo_heat)
    final_backup_demand_utility = final_hd_utility * (1. - share_of_teo_heat)

    # Add final demands to the bookkeeper
    bookkeeper.add_final_heat_demand(neighbourhood, 'TEO',
                                     useful_hd_residences,
                                     useful_hd_utility)
    bookkeeper.add_final_heat_demand(neighbourhood, 'backup',
                                     final_backup_demand_residences,
                                     final_backup_demand_utility)

    return True

def gas_available(neighbourhood, heating_option, bookkeeper, heat_type):
    """
    Checks if there is enough gas available to meet the future heat demand of
    the neighbourhood. If so, increase the used_renewable_gas variable, and
    update the bookkeeper.
    """

    # Calculate future heat demand for residences
    final_gas_demand_residences, useful_heat_demand_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
        bookkeeper, heating_option)

    # Calculate future heat demand for utility
    final_gas_demand_utility, useful_heat_demand_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
        bookkeeper, heating_option)

    # Calculate future heat demand for the two combined
    final_gas_demand = (final_gas_demand_residences +
                         final_gas_demand_utility)

    # Check if there is enough gas left to meet the neighbourhood's heat demand
    remaining_gas = config.current_project.current_scenario[
        'renewable_gas_budget'] - config.current_project.current_scenario['used_renewable_gas']

    if remaining_gas > final_gas_demand:
        # If so, increase used renewable gas
        config.current_project.current_scenario['used_renewable_gas'] += final_gas_demand

        electricity_demand_residences = (useful_heat_demand_residences * config.current_project.SPECS['electricity_share_in_heat_demand_hhp']) / config.current_project.SPECS['efficiency_electricity_to_heat']
        electricity_demand_utility = (useful_heat_demand_utility * config.current_project.SPECS['electricity_share_in_heat_demand_hhp']) / config.current_project.SPECS['efficiency_electricity_to_heat']

        # Add useful demands to the bookkeeper
        bookkeeper.add_useful_heat_demand(neighbourhood,
                                          useful_heat_demand_residences,
                                          useful_heat_demand_utility,
                                          heat_reduction_residences,
                                          heat_reduction_utility)

        # Add final demands to the bookkeeper
        bookkeeper.add_final_heat_demand(neighbourhood, heat_type,
                                         final_gas_demand_residences,
                                         final_gas_demand_utility)

        # Add final demands to the bookkeeper
        bookkeeper.add_final_heat_demand(neighbourhood, 'E',
                                         electricity_demand_residences,
                                         electricity_demand_utility)

        return True

    # If there is not enough gas available, return False
    return False


def efficiency_of_heating_option(neighbourhood, heating_option):
    """
    Returns the heat losses (in GJ) per heating option. These should be
    added to the total heat demand after insulation.

    W_MTHT: heat network losses, backup (cofiring)
    W_LT: heat network losses, backup (cofiring)
    E: efficiency electricity to heat
    H: efficiency gas to heat (both for HHP and CCB)
    """

    # Initialise the efficiency
    efficiency = 1.

    if heating_option == 'E':
        efficiency = config.current_project.SPECS['efficiency_electricity_to_heat']

    elif heating_option == 'H':
        efficiency = (neighbourhood.fraction_of_small_houses() *
                      config.current_project.SPECS['efficiency_gas_to_heat_ccb']) + (
                          (1. - neighbourhood.fraction_of_small_houses()) *
                          config.current_project.SPECS['efficiency_gas_to_heat_hhp'])

    elif heating_option == 'W_MTHT':
        # Take heat losses of heat network into account
        efficiency = config.current_project.SPECS['efficiency_of_heat_network']

    elif heating_option == 'W_LT':
        # Take heat losses of heat network into account
        efficiency = config.current_project.SPECS['efficiency_of_LT_heat_network']

    return efficiency



def add_present_heat_demand_to_bookkeeper(neighbourhood, bookkeeper):
    """
    If no heating option ()'undecided') has been assigned to a neighbourhood,
    add the present heat demand to the bookkeeper.
    """

    # Add useful demands to the bookkeeper
    bookkeeper.add_useful_heat_demand(
        neighbourhood, neighbourhood.total_heat_demand_of_residences(),
        neighbourhood.total_heat_demand_of_utility(), 0., 0.)

    # Add final demands to the bookkeeper
    bookkeeper.add_final_heat_demand(
        neighbourhood, 'undecided',
        neighbourhood.total_heat_demand_of_residences(),
        neighbourhood.total_heat_demand_of_utility())


def add_electricity_demand_to_bookkeeper(neighbourhood, bookkeeper):
    """
    After heating option 'E' has been assigned to a neighbourhood, add the
    future electricity demand to the bookkeeper.
    """

    # Calculate final heat demand for residences
    final_heat_demand_residences, useful_heat_demand_residences, heat_reduction_residences = neighbourhood.future_heat_demand_of_residences(
        bookkeeper, 'E')

    # Calculate final heat demand for utility
    final_heat_demand_utility, useful_heat_demand_utility, heat_reduction_utility = neighbourhood.future_heat_demand_of_utility(
        bookkeeper, 'E')

    # Add useful demands to the bookkeeper
    bookkeeper.add_useful_heat_demand(neighbourhood,
                                      useful_heat_demand_residences,
                                      useful_heat_demand_utility,
                                      heat_reduction_residences,
                                      heat_reduction_utility)

    # Add final demands to the bookkeeper
    bookkeeper.add_final_heat_demand(neighbourhood, 'E',
                                     final_heat_demand_residences,
                                     final_heat_demand_utility)
