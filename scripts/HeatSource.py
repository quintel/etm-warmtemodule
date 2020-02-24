class HeatSource:
    """
    Class to describe a residual (HT or LT) heat source, including its
    properties (available heat, etc.)
    """

    def __init__(self, initial_values):

        self.code = initial_values['source_id']
        self.name = initial_values['source_name']
        self.geo_coordinate = [
            initial_values['geo_coordinate_x'],
            initial_values['geo_coordinate_y']
        ]
        self.available_heat = initial_values['available_heat']
        self.neighbourhoods_in_range = initial_values[
            'neighbourhoods_in_range']

        self.used_heat = 0


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
