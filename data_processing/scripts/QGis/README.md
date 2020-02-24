### This script does the following:

1. Adds all specified shape files. Reprojects them to the same CRS (coordinate reference system)

1. Cleans up shape files (removes unnecessary attributes)

1. For each neighbourhood it adds:
   * The adjacent ('neighbouring') neighbourhoods
   * The municipality the neighbourhood is in
   * The heat sources that overlap with the neighbourhood. For each heat source a unique ID is generated. A list of IDs of overlapping heat sources is added to the neighbourhood shape file

1. Exports all relevant shape files to CSV


### How to use this script

1. Open QGIS

1. Open the Python console to see script output (_Plugins -> Python Console_)

1. Open main.py in the QGIS processing tool box (_Processing -> Toolbox -> Open Existing Script_)

1. Make sure the _project\_folder_, _geo\_scripts\_folder_ and _geo\_layer\_folder_ are correct.

1. Specify the shape files used for the analysis (_NEIGHBOURHOODS, MUNICIPALITIES, HEAT\_SOURCES_). You can specify:
   * _'path'_: The file path of the shape file
   * _'attributes\_to\_keep'_: The attributes you want to keep (to see the attributes of a layer go to _Layer -> Add Layer -> Add Vector Layer_ -> select desired layer, then right click on it in the Layer Pane on the left -> _Open Attribute Table_)
   * _'output\_file'_: The output file path/name
   * _'id\_attribute'_: The name of the attribute that contains a unique ID for each feature (only available for the neighbourhoods and municipality layers)
   * _'id\_prefix'_: The prefix used when generating unique IDs for the heat sources. E.g. _'HTHP'_ will add unique IDs _'HTHP0001', 'HTHP0002'_ etc. to the heat sources in a layer (only available to heat source shape files)
   * _'column'_: The column name added to the neighbourhood layer containing the overlapping heat sources for each neighbourhood. E.g. the column _'HT\_HIGH'_ will contain the IDs of all high temperature heat sources in the high potential shape file (only available to heat source shape files)

6. Run the script (_green '>' button_). The script takes a couple of minutes to run. If prompted for 'date transformations' hit 'Ok'. When the script is finished, you may get a warning _'Seems there is no valid script in the file'_. This is can be ignored. The output files of each layer will be saved as CSV in the folder(s) specified in step 5.


### Troubleshooting

**Q: Not all neighbourhoods have a corresponding municipality?**

**A**: Make sure the used municipality layer fully overlaps with the neighbourhood layer. For each neighbourhood a (random) point is generated that lies in the neighbourhood. The script checks in which municipality this point is located. Some neighbourhoods contain long bridges/small islands etc. The generated point may lie in these areas. If a municipality layer is used without sea/water borders, there may be no overlap with these points.

**Q: The script output shows no overlap with heat source X?**

**A**: Some features (individual neighbourhoods or heat sources) may be invalid. This is not necessarily a problem as the script tries to fix this by 'buffering' each feature before checking the overlap. However, this may not work in 100% of the cases. To check for invalid features, go to _Vector -> Geometry Tools -> Check Validity_ -> Set 'input layer' to the layer you want to check and hit _Run_. Three new layers are generated: _'Valid output'_ containing all valid features, _'Invalid output'_ containing all invalid features and _'Error output'_ containing the invalid areas (e.g. self-intersecting points).