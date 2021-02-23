class HeatSource:
    """
    Class to describe a residual (HT or LT) heat source, including its
    properties (available heat, etc.). If no available heat is given, we assume
    an endless supply (e.g. for geothermal sources)
    """

    def __init__(self, initial_values):

        self.code = initial_values['source_id']
        self.name = initial_values['source_name']
        self.geo_coordinate = [
            initial_values['geo_coordinate_x'],
            initial_values['geo_coordinate_y']
        ]
        self.neighbourhoods_in_range = initial_values['neighbourhoods_in_range']

        self.used_heat = 0

        if 'available_heat' in initial_values:
            self.available_heat = initial_values['available_heat']
        else:
            self.available_heat = 9999999.0


    def __str__(self):
        overview = ("Source {} (id: {}) \n"
                    "Heat available: {} \n"
                    "Used heat: {} \n"
                    "Geo coordinates: {} \n"
                    "Neighbourhoods in range: {}").format(
                        self.name, self.code, self.available_heat,
                        self.used_heat, self.geo_coordinate,
                        self.neighbourhoods_in_range)

        return overview
