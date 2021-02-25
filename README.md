## ETM heat module

### Introduction

The heat module of the Energy Transtion Model (ETM) has been developed as a tool that can support a user in making future scenarios for the heat supply of the built environment. The ETM heat module determines which heating technology is preferred based on the composition of the building stock per neighbourhood. The idea behind this method is that the composition of the building stock is an important factor in determining the heating technology. In addition, the housing stock is relatively stable amid all the uncertainties about the heat supply (such as price developments, efficiencies and the availability of heat sources) towards 2050. In addition to the building stock, the future availability of heat sources is also taken into account.

### Calculation steps

The following technologies are take into account:

- Low temperature heating technologies (LT):
	- All-electric: air or ground source heat pump
	- LT district heating: fed by residual heat sources with 30 degrees output temperature and lower

- Medium and high temperature heating technologies (MT / HT):
	- Renewable gas (green gas / hydrogen): HR boiler or hybrid heat pump (in combination with electricity)
	- MT / HT district heating: fed by geothermal / residual heat sources from 50 degrees output temperature or thermal energy from surface water (Dutch acronym: TEO) / thermal energy from waste water (Dutch acronym: TEA) from 30 degrees output temperature in combination with co-firing

The ETM heat module determines the preferred technology per neighbourhood according to three main steps:

1. The ETM heat module determines which heating technology is preferred based on the composition of the building stock per neighbourhood. This results in a robustness score per heating technology for each neighbourhood.
2. Scarce resources are allocated to the neighbourhoods according to this robustness score. Neighbourhoods with the highest robustness score for a scarce resource are assigned this first.

In the first part of step 1 (Step 1a), the existing building stock in the area is examined. Based on the year of construction and type of housing / utility type of the building stock, it is determined which heating technologies are suitable for this neighbourhood (see [Matrix 1](#matrix-1---renewable-gas-g-mtht-district-heating-w_mtht-and-all-electric-e-for-residences) and [Matrix 2](#matrix-2---renewable-gas-g-mtht-district-heating-w_mtht-and-all-electric-e-for-services) below). Every combination of house type / utility type and year of construction class has a preference for a specific heating technology. A total robustness score of 100% is thus divided over the three possible technologies. The result of this step is a list of heating technologies and for each technology a percentage that indicates how high this preference is.

In the second part of step 1 (Step 1b), it is checked whether or not a neighbourhood is suitable for LT district heating. This is determined by means of an extra matrices in the ETM heat module (see [Matrix 3](#matrix-3---lt-district-heating-w_lt-for-residences) and (see [Matrix 4](#matrix-4---lt-district-heating-w_lt-for-services) below). If it follows from this that the preference for LT district heating is higher than 50%, then this neighbourhood is considered suitable for LT district heating. In this step we check whether or not the neighbourhoods are suitable for LT district heating. The exact score from the LT matrix is ​​not taken into account further. Note: this threshold is adjustable: `lt_eligibility_threshold` in the config-file.

In the third part of step 1 (Step 1c), existing MT/HT district heating networks are taken into account. When the share of this network is higher than 70% of the WEQ in that neighbourhood, then the neighbourhood gets 100% preference for MT/HT district heating. When the share is between 30-70% of the WEQ, then this neighbourhood gets a slight advantage for district heating by raising the preference for MT/HT district heating with 2.5%. Note: these percentages are adjustable in the config-file.

In step 2, the preferences of the neighbourhoods are compared to the available heat supply (residual heat, geothermal energy, TEO, renewable gas, hydrogen). The neighbourhoods with the highest preference for a particular technology are allocated the corresponding resource first. The preferred percentage of that technology is then the robustness score. The resources are allocated until one resource is depleted. At that point, the neighbourhoods switch to their second choices. In the case of a second choice, the neighbourhood has a lower robustness score than if a neighbourhood was assigned its first technology choice. The order in which the heat sources are allocated to a neighbourhood are presented in the [Decision Trees](#step-2-decision-trees).

Calculation example:

- We will take a fictitious neighbourhood that consists only of houses. These consist for 75% of detached houses from before 1946 and for 25% of apartments after 2010.
- Step 1a: Matrix 1 then shows a preference for renewable gas (75%) for the detached houses and to a much lesser extent a preference for all-electric (25%) for the apartments
- Step 1b: it follows from Matrix 3 that this neighbourhood is 25% suitable for LT district heating. This is lower than 50%, so the neighbourhood is not considered suitable for LT district heating.
- Step 1c: no existing heat network in the neighbourhood, so nothing changes to robustness score.
- Step 2: the neighbourhood's preference is renewable gas. If there is still enough gas left after gas has been allocated to neighbourhoods with an even greater preference for renewable gas, this neighbourhood will end up with renewable gas with a robustness score of 75%. If, after gas has been allocated to neighbourhoods with an even greater preference for renewable gas, there is no longer enough gas available, then this neighbourhood will end up with all-electric with a robustness score of 25%.

### Step 1: Preference matrices

##### MATRIX 1 - Renewable gas (G), MT/HT district heating (W_MTHT) and all-electric (E) for residences

| Residences | < 1946 | 1946-1974 | 1975-1990 | 1991-2000 | 2001-2010 | > 2010 |
| ---------- | -------| --------- | --------- | --------- | --------- | ------ |
| Apartment | W_MTHT: 100% | W_MTHT: 67%, G: 33% | W_MTHT: 67%, G: 33% | W_MTHT: 33%, G: 67% | G: 33%, E: 67% | E: 100% |
| Terraced house | W_MTHT: 67%, G: 33% | W_MTHT: 67%, G: 33% | W_MTHT: 33%, G: 67% | G: 67%, E: 33% | G: 33%, E: 67% | E: 100% |
| Semi-detached house | G: 100% | G: 100% | G: 100% | G: 33%, E: 67% | G: 33%, E: 67% | E: 100% |
| Detached house | G: 100% | G: 100% | G: 100% | G: 67%, E: 33% | G: 33%, E: 67% | E: 100% |

##### MATRIX 2 - Renewable gas (G), MT/HT district heating (W_MTHT) and all-electric (E) for services

| Services | <1990 | 1991-2000 | >2000 |
| -------- | ----- | --------- | ----- |
| < 200 m<sup>2</sup> | Follow residences | Follow residences | E: 100% |
| 200 - 2000 m<sup>2</sup> | Follow residences | Follow residences | E: 100% |
| > 2000 m<sup>2</sup> | W_MTHT: 100% | W_MTHT: 67%, E: 33% | E: 100% |

##### MATRIX 3 - LT district heating (W_LT) for residences

| Residences | < 1946 | 1946-1974 | 1975-1990 | 1991-2000 | 2001-2010 | > 2010 |
| ---------- | -------| --------- | --------- | --------- | --------- | ------ |
| Apartment |  |  |  | W_LT: 33% | W_LT: 67% | W_LT: 100% |
| Terraced house |  |  |  || W_LT: 33% | W_LT: 67% |
| Semi-detached house |  |  |  |  |  |  |
| Detached house |  |  |  |  |  |  |

##### MATRIX 4 - LT district heating (W_LT) for services

| Services | <1990 | 1991-2000 | >2000 |
| -------- | ----- | --------- | ----- |
| < 200 m<sup>2</sup> | Follow residences | Follow residences | W_LT: 50%|
| 200 - 2000 m<sup>2</sup> | Follow residences | Follow residences | W_LT: 100%|
| > 2000 m<sup>2</sup> |  | W_LT: 33% |W_LT: 100% |

The user is free to adjust the percentages of the matrices in the config files.

### Step 2: Decision trees

![Decision tree first choice](img/Beslisboom%201e%20keus%20openingsbod%202021%20v0.3%20EN.png)

![Decision tree second choice](img/Beslisboom%202e%20keus%20openingsbod%202021%20v0.3%20EN.png)

### Getting started

Install the `requirements.txt` by typing the following command in the terminal (for Python3):
```pip3 install -r requirements.txt```

Furthermore, make sure you have the QGIS application installed on your machine.


### Processing the raw data

Before we can run the heat module, the raw data has to be processed in order to generate the input data in the correct format for the heat module scripts. There are a few data processing scripts that have to be run:

* `data_processing` ▸ `⁨scripts` ▸ `QGis` ▸ `main.py`
* `data_processing` ▸ `⁨scripts` ▸ `Pandas` ▸ `households_input_data_transformation.py`
* `data_processing` ▸ `⁨scripts` ▸ `Pandas` ▸ `buildings_input_data_transformation.py`
* `data_processing` ▸ `⁨scripts` ▸ `Pandas` ▸ `generate_neighbourhood_properties.py`

For each script, a short description is provided.

#### main.py

The `main.py` script should be imported into QGIS and run from there. The exact steps for this can be read `data_processing` ▸ `⁨scripts` ▸ `QGis` ▸ `README.md`.  Before running the script, make sure the  `data_processing`⁩ ▸ ⁨`geo_layers⁩` ▸ `⁨reprojected` directory exists. In the `data_processing`⁩ ▸ ⁨`projects` directory the raw data for the different projects is stored. Before running the script, make sure the correct `BAG` and `geo_layers` directories are copied into the `data_processing` root directory.

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
| \< teo\_sources\_high\_potential \> | data\_processing ▸ ⁨geo\_layers ▸ heat\_sources ▸ high\_potential | Shapefile in which the high potential availability of residual TEO is defined. Make sure the correct file name is specified in `main.py`. |

The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| geothermal\_sources\_high\_potential.csv | input_data |
| geothermal\_sources\_low\_potential.csv | input_data |
| ht\_sources\_high\_potential.csv | input_data |
| ht\_sources\_low\_potential.csv | input_data |
| lt\_sources\_high\_potential.csv | input_data |
| lt\_sources\_low\_potential.csv | input_data |
| teo\_sources\_high\_potential.csv | input_data |
| neighbourhoods_geo.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

Note: the outputfiles with the heat sources should contain a column named `available_heat` with the available heat in Giga Joule to be able to run the main heat module. For OB2021 we have calculated the available heat based on the installed capacity and 8760 full load hours and added this to the shapefiles of the heat sources. When no `available_heat`column is given in the output files, then the main heat module will automatically add a heat demand of 9999999.0 GJ (see [this commit](https://github.com/quintel/etm-warmtemodule/commit/daf28c8a0e3a5f007ee6b486054779a1d99e4c16))

#### households\_input\_data\_transformation.py

Below, you can find an overview of the required input data:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| epi\_per\_label.csv | data_processing ▸ ⁨BAG ▸ general | Based on data in energy model [VESTA](https://github.com/RuudvandenWijngaart/VestaDV/tree/Vesta40/data)|
| housing\_types.csv | data_processing ▸ ⁨BAG ▸ households | Based on types used in energy model [VESTA](https://github.com/RuudvandenWijngaart/VestaDV/tree/Vesta40/data) |
| vesta\_generic\_labels\_households.csv | data_processing ▸ ⁨BAG ▸ households | |
| \<BAG file with all residential objects>| data_processing ▸ ⁨BAG ▸ households | CSV-file with all residential objects including BAG specifications and neighbourhood|

The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| housing\_stock\_size\_year\_per\_neighbourhood.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

#### buildings\_input\_data\_transformation.py

This script processes the BAG files with all individual objects and sorts the objects into the categories used in the preference matrices. Additionally, this scripts calculates the average energy label for each category.

Below, you can find an overview of the required input data:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| epi\_per\_label.csv | data_processing ▸ ⁨BAG ▸ general | Based on data in energy model [VESTA](https://github.com/RuudvandenWijngaart/VestaDV/tree/Vesta40/data) |
| \<EP online download with all offical labels>| data_processing ▸ ⁨BAG ▸ general | This file can be downloaded [here](https://www.ep-online.nl/ep-online/PublicData)|
| building\_types.csv | data_processing ▸ ⁨BAG ▸ buildings | Based on types used in energy model [VESTA](https://github.com/RuudvandenWijngaart/VestaDV/tree/Vesta40/data)|
| vesta\_generic\_labels\_buildings.csv | data_processing ▸ ⁨BAG ▸ buildings | Based on labels used in energy model [VESTA](https://github.com/RuudvandenWijngaart/VestaDV/tree/Vesta40/data) |
| \<BAG file with all utility objects>| data_processing ▸ ⁨BAG ▸ buildings | CSV-file with all utility objects including BAG specifications and neighbourhood|

The output of this script is as follows:

| Output file | Path |
| ----------- | ---- |
| buildings\_stock\_type\_year\_per\_neighbourhood.csv | input_data |

Make sure you move these output files to the correct project directory: `input_data` ▸ `< project_name >`.

#### generate\_neighbourhood\_properties.py

This script generates the neighbourhood properties file for your project. You simply run `python3 data_processing/scripts/Pandas/generate_heighbourhood_properties.py <PROJECT>`, where `<PROJECT>` is the name of your project (e.g. sample). Make sure you have the following files in your `input_data/<project_name>` folder:

| Input file | Path | Comment |
| ---------- | ---- | ------- |
| neighbourhood_list.csv | `input_data` ▸ `<project_name>` | Neighbourhoods for which the heat module and preprocessing should be run. |
| neighbourhood_heat_demand.csv |  `input_data` ▸ `<project_name>` | Contains info on demand (Giga Joule / house-equivalent) for different heating technologies. For OB2021 we have used VESTA neighbourhood demands |
| existing_heat_network_share.csv | `input_data` ▸ `<project_name>` | Specifies the percentage of objects already attached to a heat network per neighbourhood |

You may also skip this step and create the neighbourhood properties file yourself. Please look at [the sample file](input_data/sample/neighbourhood_properties.csv) for the required fields.

### Running the main heat module

The main module is run by executing `main.py` in the `scripts` folder. Make sure
the preprocessing is done before you start: the files described in the previous step should be
present in the `input_data` folder, and they should be loaded by running `load_data.py`.

The module should be run for a specific project (e.g. sample), and scenario (e.g. scenario_1):
```
python3 scripts/load_data.py <PROJECT> <SCENARIO>
python3 scripts/main.py <PROJECT> <SCENARIO>
```
#### Input and configuration

You can adjust any thresholds, matrices and other configurables in
[a config file for your project](scripts/config_files/sample.py). This is also the place where you can specify your scenarios (starting on line 108).

All input files can be generated from the preprocessing steps described above.

#### Output

The module will generate a file called `neighbourhoods_output.csv` in your project folder in `output_data` . This csv contains one column *assigned_heating_option* specifiying the heat option recommended by the heat module. Other columns show the information this decision was made on, or show more detail on the assigned option. 
Note: the energy demands in the output files have the same unit as the energy values used as input, in our case Giga Joule. 
