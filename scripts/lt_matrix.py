from Matrix import Matrix
import config

class LTMatrix(Matrix):
    '''
    The LT Matrix represents a Matrix that has only one heat_option. Instead of
    returning multiple sorted options. It just returns a 1 or 0 depending on the
    one option being higher than a certain threshold.
    '''
    def __init__(self):
        super().__init__(number_of_options=2)
        self.residences_matrix = config.current_project.LT_MATRIX_RESIDENCES
        self.utility_matrix = config.current_project.LT_MATRIX_UTILITY
        self.threshold = config.current_project.ASSUMPTIONS['lt_eligibility_threshold']

    def sorted_preference(self, neighbourhood):
        '''
        Returns the sorted peference for the given neighbourhood
        '''
        if self.normalized_vector[0] > self.threshold:
            return { 'W_LT': 1 }

        return { 'W_LT': 0 }
