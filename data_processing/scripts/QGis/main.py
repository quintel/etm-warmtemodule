import os
import sys

from importlib import reload

# folder where project is located
project_folder = os.path.expanduser('~/') + 'Projects/etm-warmtemodule/'

# root folder where scripts are located
geo_scripts_folder = 'data_processing/scripts/QGis/'
# root folder where shape files are located
geo_layer_folder = 'data_processing/geo_layers/'

# insert path to import modules
sys.path.insert(0, project_folder + geo_scripts_folder)

import layer_management
import spatial_analysis

reload(layer_management)
reload(spatial_analysis)

# set CRS. All layers are reprojected to this CRS. EPSG:28992 is standard projection for the Netherlands with unit meters
CRS = 'EPSG:28992'

# specify layers
NEIGHBOURHOODS = {
    'path' :'area/2019Buurten_in_gebied_StedinEndurisWI.shp',
    'rename_attributes': {
                            'BU_CODE': 'neighbourhood_code',
                            'BU_NAAM': 'neighbourhood_name'
                             },
    'attributes_to_keep': ['neighbourhood_code', 'neighbourhood_name'],
    'identifier': 'NEIGH',
    'output_file': 'neighbourhoods_geo.csv'
    }

MUNICIPALITIES = {
    'path' :'area/2019Gemeenten_in_gebied_StedinEndurisWI.shp',
    # attribute containing unique municipality code
    'id_attribute': 'GM_CODE',
    # if municipality code consists of only numbers, we can add a prefix, e.g. 'GM'
    'code_prefix' : 'GM',
    # attribute containing municipality name
    'name_attribute' : 'GM_NAAM',
    'identifier' : 'MUNIC'
    }

HEAT_SOURCES = {
    'HT_HIGH_POTENTIAL' : {
        'path': 'heat_sources/high_potential/MT_SEW_ruim_leveringsgebieden_incl_wsw.shp',
        'rename_attributes': {
                                'bron_naam': 'source_name',
                                'MWcapacite': 'available_heat'
                             },
        'attributes_to_keep': ['source_name', 'available_heat'],
        'identifier': 'HTHP',
        'output_file': 'ht_sources_high_potential.csv'
        },
    'HT_LOW_POTENTIAL' : {
        'path': 'heat_sources/low_potential/MT_SEW_beperkt_leveringsgebieden_incl_wsw.shp',
        'rename_attributes': {
                                'bron_naam': 'source_name',
                                'MWcapacite': 'available_heat'
                             },
        'attributes_to_keep': ['source_name', 'available_heat'],
        'identifier': 'HTLP',
        'output_file' : 'ht_sources_low_potential.csv'
        },
    'LT_HIGH_POTENTIAL' : {
        'path': 'heat_sources/high_potential/LT_SEW_ruim_leveringsgebieden.shp',
        'rename_attributes': {
                                'bron_naam': 'source_name',
                                'MWcapacite': 'available_heat'
                             },
        'attributes_to_keep': ['source_name', 'available_heat'],
        'identifier': 'LTHP',
        'output_file' : 'lt_sources_high_potential.csv'
        },
    'LT_LOW_POTENTIAL' : {
        'path': 'heat_sources/low_potential/LT_SEW_beperkt_leveringsgebieden.shp',
        'rename_attributes': {
                                'bron_naam': 'source_name',
                                'MWcapacite': 'available_heat'
                             },
        'attributes_to_keep': ['source_name', 'available_heat'],
        'identifier': 'LTLP',
        'output_file' : 'lt_sources_low_potential.csv'
        },
    'GEOTHERMAL_HIGH_POTENTIAL' : {
        'path': 'heat_sources/high_potential/GEO_ruim_StedinEndurisWestlandInfra.shp',
        'rename_attributes': {
                                'name': 'source_name'
                             },
        'attributes_to_keep': ['source_name'],
        'identifier': 'GEOHP',
        'output_file' : 'geothermal_sources_high_potential.csv'
        },
    'GEOTHERMAL_LOW_POTENTIAL' : {
        'path': 'heat_sources/low_potential/GEO_beperkt_StedinEndurisWestlandInfra.shp',
        'rename_attributes': {
                                'capacity': 'available_heat'
                             },
        'attributes_to_keep': ['source_name'],
        'identifier': 'GEOLP',
        'output_file' : 'geothermal_sources_low_potential.csv'
        },
    'TEO_HIGH_POTENTIAL' : {
        'path': 'heat_sources/high_potential/TEO_Potentiekaart_StedinEndurisWestlandInfra_Buffer1km_Contour500m.shp',
        'rename_attributes': {
                                'name': 'source_name'
                             },
        'attributes_to_keep': ['source_name'],
        'identifier': 'TEOHP',
        'output_file' : 'teo_sources_high_potential.csv'
        }
    }


# add neighbourhoods layer
neighbourhoods_layer = layer_management.add_layer_as_reprojected_gpkg(project_folder, geo_layer_folder, NEIGHBOURHOODS['path'], CRS, 'reprojected/{}'.format(NEIGHBOURHOODS['identifier']))

# rename attributes
layer_management.rename_attributes(neighbourhoods_layer, NEIGHBOURHOODS['rename_attributes'])

# clean up neighbourhoods layer
layer_management.delete_all_attributes_except(NEIGHBOURHOODS['attributes_to_keep'], neighbourhoods_layer)

# for each neighbourhood find surrounding neighbourhoods
spatial_analysis.add_adjacent_features(neighbourhoods_layer, 'adjacent_neighbourhoods', 'neighbourhood_code')

# add geo coordinates to neighbourhoods layer
spatial_analysis.add_coordinates(neighbourhoods_layer)

# add municipality layer
municipality_layer = layer_management.add_layer_as_reprojected_gpkg(project_folder, geo_layer_folder, MUNICIPALITIES['path'], CRS, 'reprojected/{}'.format(MUNICIPALITIES['identifier']))

# add corresponding municipality code to each neighbourhood
spatial_analysis.add_overlapping_features(neighbourhoods_layer, municipality_layer, 'municipality_code', MUNICIPALITIES['id_attribute'], area_to_point=True, prefix = MUNICIPALITIES['code_prefix'])

spatial_analysis.add_overlapping_features(neighbourhoods_layer, municipality_layer, 'municipality_name', MUNICIPALITIES['name_attribute'], area_to_point=True)

# loop over heat source files
for NAME, SOURCE in HEAT_SOURCES.items():
    print(NAME)
    # add heat source layers
    heat_layer = layer_management.add_layer_as_reprojected_gpkg(project_folder, geo_layer_folder, SOURCE['path'], CRS, 'reprojected/{}'.format(SOURCE['identifier']))

    # rename attributes
    layer_management.rename_attributes(heat_layer, SOURCE['rename_attributes'])

    #clean up layer
    layer_management.delete_all_attributes_except(SOURCE['attributes_to_keep'], heat_layer)

    # generate unique ID for each heat source
    layer_management.add_unique_id(heat_layer, 'source_id', SOURCE['identifier'])

    # add geo coordinates
    spatial_analysis.add_coordinates(heat_layer)

    # add heat source IDs to neighbourhoods if heat source overlaps with neighbourhood
    spatial_analysis.add_overlapping_features(heat_layer, neighbourhoods_layer, 'neighbourhoods_in_range', 'neighbourhood_code')

    # export to CSV
    layer_management.export_to_csv(heat_layer, project_folder, 'input_data/', SOURCE['output_file'])

# export neighbourhoods layer to CSV
layer_management.export_to_csv(neighbourhoods_layer, project_folder, 'input_data/', NEIGHBOURHOODS['output_file'])
