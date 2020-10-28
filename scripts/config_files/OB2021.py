"""
<name of project>

This is an example of a config file. Duplicate and rename the file for your
project. Here, you may write a short description of the project.

The values of the ASSUMPTIONS and SPECS may be changed. The values of the
KEY_FIGURES don't have to be adjusted.

Furthermore, different scenarios can be distinguished. For each scenario, its
limitations, budgets, and input files (for the heat sources) can be specified.

The DEFAULT_MATRIX_RESIDENCES, DEFAULT_MATRIX_UTILITY, and NEIGHBOURHOOD_CSVS
don't have to be adjusted.
"""

ASSUMPTIONS = {
    # The confidence assigned to neighbourhoods with insufficient data that are
    # filtered in the pre-analysis
    'pre_analysis_confidence': 0,

    # The threshold for the fraction of LT eligible residences (as specified
    # in the LT Matrix) in a neighbourhood: if the threshold is exceeded,
    # the neighbourhood will get a preference checkmark for W_LT
    'lt_eligibility_threshold': 0.5,

    # The offset for the heating option preference vector: based on the linear
    # heat density, the neighbourhood's preference for a heat network may be
    # increased with a maximum of the offset
    'linear_heat_density_max_offset': 0.05,

    # For each heating option, a desired Energy Performance Index (EPI) is
    # assumed: this EPI corresponds to an amount of (relative) heat reduction,
    # specified in the KEY_FIGURES
    # source: https://keuzehulpduurzaamverwarmen.nl/poster/
    'desired_epi': {
        'W_MTHT': 1.95,  # label D
        'H': 1.95,   # label D
        'E': 1.2,   # label A/B
        'W_LT': 1.2 # label A/B
    },

    # Neighbourhoods that have existing heat networks are set to have preference
    # 100% when the existing heat networks cover more than 'threshold_high' of
    # the neighbourhood. They get an extra 'favour' preference when the coverage
    # is in between 'threshold_high' and 'threshold_low'
    'heat_network_coverage_threshold_high': 70.0,
    'heat_network_coverage_threshold_low': 30.0,
    'heat_network_coverage_favour': 0.025,

    # Future efficiency of appliances (baseload electricity demand)
    'efficiency_of_appliances': 1.0, # assuming no efficiency improvement for OB2021
}

SPECS = {
    # For each type of heat (HT and LT residual, and geothermal heat), specify
    # its share in the heat network. The remaining share (peak demand) should
    # be provided by a back-up heater.
    'share_of_HT_heat': 0.8,
    'share_of_LT_heat_for_W_MTHT': 0.4,
    'share_of_LT_heat_for_W_LT': 0.7, # source: CE Delft
    'share_of_geothermal_heat': 0.7, # source: CE Delft
    'share_of_TEO_heat': 0.7, # source: CE Delft
    'share_of_undefined_heat': 0.7, # source: CE Delft

    # Efficiencies of different heating options (heat network, central combi
    # boiler (ccb), heat pump)
    'efficiency_of_heat_network': 0.75, # 25% distribution losses, source: TKI Urban Energy (20-30%)
    'efficiency_of_LT_heat_network': 0.85, # 15% distribution losses, source: CE Delft
    'efficiency_gas_to_heat_ccb': 1.067,  # source: ETM
    'efficiency_electricity_to_heat': 3.75, # source: CE Delft

    # Efficiency for hybrid heat pump (hhp) is based on guestimates for the
    # effective COP for hot water and space heating combined (assumption: 47%
    # of space heating and 100% of hot water supplied by gas component).
    # On average 42 GJ space heating demand and 7 GJ hot water demand:
    # (42 + 7) / (0.47 * 42 + 7 ) = 1.8
    'efficiency_gas_to_heat_hhp': 1.8,

    # Share of electricity in heat demand of hybrid heat pump
    # (assumption: label C)
    'electricity_share_in_heat_demand_hhp': 0.47, # source: CE Delft
}

KEY_FIGURES = {
    # 150 m2 = 1 house (1/150 = 0.0067)
    'm2_utility_to_house_equivalents': 0.0067,

    # 1 GJ = 0.28 MWh
    'gj_to_mwh': 0.28,

    # Mapping from EPI to relative heat demand reduction (compared to a 'low'
    # insulation house). The EPI values are lower bounds (2.7 and up is label G,
    # 0% reduction, 2.41-2.7 is label F, 3% reduction etc.)
    'epi_reduction_table': {
        'residences': [
            ('-10.0', 0.68), ('0.41', 0.57), ('0.61', 0.45), ('0.81', 0.36),
            ('1.21', 0.27), ('1.41', 0.19), ('1.81', 0.12), ('2.11', 0.06),
            ('2.41', 0.03), ('2.7', 0.0), ('10.0', 0.0)
        ],
        'utility': [
            ('-10.0', 0.74), ('0.81', 0.64), ('1.21', 0.54), ('1.41', 0.46),
            ('1.81', 0.31), ('2.11', 0.0), ('10.0', 0.0)
        ]
    },
}

# Different scenarios that are run by the ETM heat module
SCENARIOS = {
    'scenario_1': { # ruim gas, ruim warmte
        'renewable_gas_budget': 99999.E6,  # in GJ
        'used_renewable_gas': 0.,
        'ht_heat': 'ht_sources_high_potential.csv',
        'lt_heat': 'lt_sources_high_potential.csv',
        'geothermal': 'geothermal_sources_high_potential.csv',
        'teo': 'teo_sources_high_potential.csv'
    },
    'scenario_2': { # beperkt gas, ruim warmte
        'renewable_gas_budget': 6.485E6,  # in GJ
        'used_renewable_gas': 0.,
        'ht_heat': 'ht_sources_high_potential.csv',
        'lt_heat': 'lt_sources_high_potential.csv',
        'geothermal': 'geothermal_sources_high_potential.csv',
        'teo': 'teo_sources_high_potential.csv'
    },
    'scenario_3': { # beperkt gas, beperkt warmte
        'renewable_gas_budget': 6.485E6,  # in GJ
        'used_renewable_gas': 0.,
        'ht_heat': 'ht_sources_low_potential.csv',
        'lt_heat': 'lt_sources_low_potential.csv',
        'geothermal': 'geothermal_sources_low_potential.csv',
        'teo': 'teo_sources_no_potential.csv'
    },
    'scenario_4': { # beperkt gas, geen geothermie, onbeperkt restwarmte
        'renewable_gas_budget': 6.485E6,  # in GJ
        'used_renewable_gas': 0.,
        'ht_heat': 'ht_sources_unlimited_potential.csv',
        'lt_heat': 'lt_sources_unlimited_potential.csv',
        'geothermal': 'geothermal_sources_no_potential.csv',
        'teo': 'teo_sources_no_potential.csv'
    }
}

# Default residences matrix
# [heat network ('W_MTHT'), hybrid/renewable gas ('H'), all-electric ('E')]
DEFAULT_MATRIX_RESIDENCES = {
    'Apartment': {
        '<1946': [1.0, 0.0, 0.0],
        '1946-1974': [0.67, 0.33, 0.0],
        '1975-1990': [0.33, 0.67, 0.0],
        '1991-2000': [0.33, 0.67, 0.0],
        '2001-2010': [0.0, 0.33, 0.67],
        '>2010': [0.0, 0.0, 1.0]
    },
    'Terraced house': {
        '<1946': [0.67, 0.33, 0.0],
        '1946-1974': [0.33, 0.67, 0.0],
        '1975-1990': [0.33, 0.67, 0.0],
        '1991-2000': [0.0, 0.67, 0.33],
        '2001-2010': [0.0, 0.33, 0.67],
        '>2010': [0.0, 0.0, 1.0]
    },
    'Semi-detached house': {
        '<1946': [0.0, 1.0, 0.0],
        '1946-1974': [0.0, 1.0, 0.0],
        '1975-1990': [0.0, 1.0, 0.0],
        '1991-2000': [0.0, 0.33, 0.67],
        '2001-2010': [0.0, 0.33, 0.67],
        '>2010': [0.0, 0.0, 1.0]
    },
    'Detached house': {
        '<1946': [0.0, 1.0, 0.0],
        '1946-1974': [0.0, 1.0, 0.0],
        '1975-1990': [0.0, 1.0, 0.0],
        '1991-2000': [0.0, 0.67, 0.33],
        '2001-2010': [0.0, 0.33, 0.67],
        '>2010': [0.0, 0.0, 1.0]
    }
}

# Default utility matrix
# [heat network ('W_MTHT'), hybrid/renewable gas ('H'), all-electric ('E'),
#  follow housing stock]
DEFAULT_MATRIX_UTILITY = {
    'Small': {
        '<1991': [0.0, 0.0, 0.0, 1.0],
        '1991-2000': [0.0, 0.0, 0.0, 1.0],
        '>2000': [0.0, 0.0, 1.0, 0.0]
    },
    'Medium': {
        '<1991': [0.0, 0.0, 0.0, 1.0],
        '1991-2000': [0.0, 0.0, 0.0, 1.0],
        '>2000': [0.0, 0.0, 1.0, 0.0]
    },
    'Large': {
        '<1991': [1.0, 0.0, 0.0, 0.0],
        '1991-2000': [0.67, 0.0, 0.33, 0.0],
        '>2000': [0.0, 0.0, 1.0, 0.0]
    }
}

# Default lt residences matrix
# [lt heat network ('W_LT'), nothing]
LT_MATRIX_RESIDENCES = {
    'Apartment': {
        '<1946': [0.0, 1.0],
        '1946-1974': [0.0, 1.0],
        '1975-1990': [0.0, 1.0],
        '1991-2000': [0.33, 0.67],
        '2001-2010': [0.67, 0.33],
        '>2010': [1.0, 0.0]
    },
    'Terraced house': {
        '<1946': [0.0, 1.0],
        '1946-1974': [0.0, 1.0],
        '1975-1990': [0.0, 1.0],
        '1991-2000': [0.0, 1.0],
        '2001-2010': [0.33, 0.67],
        '>2010': [0.67, 0.33]
    },
    'Semi-detached house': {
        '<1946': [0.0, 1.0],
        '1946-1974': [0.0, 1.0],
        '1975-1990': [0.0, 1.0],
        '1991-2000': [0.0, 1.0],
        '2001-2010': [0.0, 1.0],
        '>2010': [0.0, 1.0]
    },
    'Detached house': {
        '<1946': [0.0, 1.0],
        '1946-1974': [0.0, 1.0],
        '1975-1990': [0.0, 1.0],
        '1991-2000': [0.0, 1.0],
        '2001-2010': [0.0, 1.0],
        '>2010': [0.0, 1.0]
    }
}

# Default utility matrix
# [heat network ('W_LT'), nothing, follow housing stock]
LT_MATRIX_UTILITY = {
    'Small': {
        '<1991': [0.0,0.0, 1.0],
        '1991-2000': [0.0, 0.0, 1.0],
        '>2000': [0.5, 0.5, 0.0]
    },
    'Medium': {
        '<1991': [0.0, 0.0, 1.0],
        '1991-2000': [0.0, 0.0, 1.0],
        '>2000': [1.0, 0.0, 0.0]
    },
    'Large': {
        '<1991': [0.0, 1.0, 0.0],
        '1991-2000': [0.33, 0.67, 0.0],
        '>2000': [1.0, 0.0, 0.0]
    }
}



# CSV files with neighbourhood data
NEIGHBOURHOOD_CSVS = {
    'list': 'neighbourhood_list.csv',
    'properties': [
        'neighbourhood_properties.csv',
        'neighbourhoods_geo.csv'
    ],
    'housing_stock': 'housing_stock_type_year_per_neighbourhood.csv',
    'utility_stock': 'building_stock_size_year_per_neighbourhood.csv'
}


def set_current_scenario(scenario_name):

    global current_scenario
    global current_scenario_name

    current_scenario = SCENARIOS[scenario_name]
    current_scenario_name = scenario_name

    return current_scenario, current_scenario_name
