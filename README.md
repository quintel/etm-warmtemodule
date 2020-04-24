## ETM heat module

ETM's heat module has been developed as a tool that can support a user in making future scenarios for the heat supply of the built environment. Given certain conditions (such as the future availability of green gas) the ETM heat module assigns a heating technology (all-electric, renewable gas, or district heating) to a neighbourhood based on its building stock (see the paragraph on the preference matrices). A decision tree is used in assigning the heating technologies which makes sure the coherence between neighbourhoods within the geographical scope is taken into account.

### Preference matrices

TODO - Add a short introduction about the matrices.

The default preference matrices for residences and services are as follows:

| Residences | < 1946 | 1946-1974 | 1975-1990 | 1991-2000 | 2001-2010 | > 2010 |
| ---------- | -------| --------- | --------- | --------- | --------- | ------ |
| Apartment | W: 100% | W: 67%, G: 33% | W: 67%, G: 33% | W: 33%, G: 67% | G: 33%, E: 67% | E: 100% |
| Terraced house | W: 67%, G: 33% | W: 67%, G: 33% | W: 33%, G: 67% | G: 67%, E: 33% | G: 33%, E: 67% | E: 100% |
| Semi-detached house | G: 100% | G: 100% | G: 100% | G: 33%, E: 67% | G: 33%, E: 67% | E: 100% |
| Detached house | G: 100% | G: 100% | G: 100% | G: 67%, E: 33% | G: 33%, E: 67% | E: 100% |

| Services | <1990 | 1991-2000 | >2000 |
| -------- | ----- | --------- | ----- |
| < 200 m<sup>2</sup> | Follow residences | Follow residences | E: 100% |
| 200 - 2000 m<sup>2</sup> | Follow residences | Follow residences | E: 100% |
| > 2000 m<sup>2</sup> | W: 100% | W: 67%, E: 33% | E: 100% |

Note that "E" stands for all-electric, "G" stands for renewable gas, and "W" stands for district heating.

The user is free to adjust the percentages of the matrices in the config files.

### Decision tree

TODO


### Getting started

Install the `requirements.txt`

Furthermore, make sure you have the QGIS application installed on your machine.


### Processing the raw data

Before we can run the heat module, the raw data has to be processed in order to generate the input data in the correct format for the heat module scripts. There are a few data processing scripts that have to be run:

* `data_processing` ▸ `⁨scripts` ▸ `QGis` ▸ `main.py`
* `data_processing` ▸ `⁨scripts` ▸ `Pandas` ▸ `households_input_data_transformation.py`
* `data_processing` ▸ `⁨scripts` ▸ `Pandas` ▸ `buildings_input_data_transformation.py`

For each script, a short description is provided.

#### main.py

The `main.py` script should be imported into QGIS and run from there. Before running the script, make sure the  `data_processing`⁩ ▸ ⁨`geo_layers⁩` ▸ `⁨reprojected` directory exists. In the `data_processing`⁩ ▸ ⁨`projects` directory the raw data for the different projects is stored. Before running the script, make sure the correct `BAG` and `geo_layers` directories are copied into the `data_processing` root directory.

Below, you can find an overview of the required input data:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| building\_types.csv | data_processing ▸ ⁨BAG ▸ buildings | |
| vesta\_generic\_labels\_buildings.csv | data_processing ▸ ⁨BAG ▸ buildings | |
| epi\_per\_label.csv | data_processing ▸ ⁨BAG ▸ general | |
| housing\_types.csv | data_processing ▸ ⁨BAG ▸ households | |
| vesta\_generic\_labels\_households.csv | data_processing ▸ ⁨BAG ▸ households | |
| \< municipalities \> | data\_processing ▸ ⁨geo\_layers ▸ area | Shapefile in which the municipalities are defined. Make sure the correct file name is specified in `main.py`. |
| \< neighbourhoods \> | data\_processing ▸ ⁨geo\_layers ▸ area | Shapefile in which the neighbourhoods are defined. Make sure the correct file name is specified in `main.py`. |
| \< geothermal\_sources\_low\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ low\_potential | Shapefile in which the low potential availability of geothermal sources is defined. Make sure the correct file name is specified in `main.py`. |
| \< ht\_sources\_low\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ low\_potential | Shapefile in which the low potential availability of residual HT sources is defined. Make sure the correct file name is specified in `main.py`. |
| \< lt\_sources\_low\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ low\_potential | Shapefile in which the low potential availability of residual LT sources is defined. Make sure the correct file name is specified in `main.py`. |
| \< geothermal\_sources\_high\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ high\_potential | Shapefile in which the high potential availability of geothermal sources is defined. Make sure the correct file name is specified in `main.py`. |
| \< ht\_sources\_high\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ high\_potential | Shapefile in which the high potential availability of residual HT sources is defined. Make sure the correct file name is specified in `main.py`. |
| \< lt\_sources\_high\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ high\_potential | Shapefile in which the high potential availability of residual LT sources is defined. Make sure the correct file name is specified in `main.py`. |

The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| geothermal\_sources\_high\_potential.csv | input_data |
| geothermal\_sources\_low\_potential.csv | input_data |
| ht\_sources\_high\_potential.csv | input_data |
| ht\_sources\_low\_potential.csv | input_data |
| lt\_sources\_high\_potential.csv | input_data |
| lt\_sources\_low\_potential.csv | input_data |
| neighbourhoods_geo.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

#### households\_input\_data\_transformation.py

Script

Below, you can find an overview of the required input data:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| epi\_per\_label.csv | data_processing ▸ ⁨BAG ▸ general | |
| housing\_types.csv | data_processing ▸ ⁨BAG ▸ households | |
| vesta\_generic\_labels\_households.csv | data_processing ▸ ⁨BAG ▸ households | |

The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| housing\_stock\_size\_year\_per\_neighbourhood.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

#### buildings\_input\_data\_transformation.py

Below, you can find an overview of the required input data:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| epi\_per\_label.csv | data_processing ▸ ⁨BAG ▸ general | |
| building\_types.csv | data_processing ▸ ⁨BAG ▸ buildings | |
| vesta\_generic\_labels\_buildings.csv | data_processing ▸ ⁨BAG ▸ buildings | |


The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| buildings\_stock\_type\_year\_per\_neighbourhood.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

### Running the heat module script

Script

Input

Output
