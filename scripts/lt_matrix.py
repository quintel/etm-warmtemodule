from Matrix import Matrix
import config

class LTMatrix(Matrix):
    '''
    The LT Matrix represents a Matrix that has only one heat_option. Instead of
    returning multiple sorted options. It just returns a 1 or 0 depending on the
    one option being higher than a certain threshold.
    '''
    def __init__(self):
        super().__init__(number_of_options=1)
        self.residences_matrix = config.current_project.LT_MATRIX_RESIDENCES
        self.utility_matrix = config.current_project.LT_MATRIX_UTILITY
        self.threshold = config.current_project.LT_THRESHOLD

    def sorted_preference(self, neighbourhood):
        '''
        Returns the sorted peference for the given neighbourhood
        '''

        if self.normalized_vector[0] > self.threshold:
            return { 'W_LT': True }

        return { 'W_LT': False }
