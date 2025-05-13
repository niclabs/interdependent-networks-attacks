
class SoilMap(object):
    """ Object in charge of handling information regarding the soil
    properties for a given map.

    This object is meant to be used by SeismicAttack objects.

    """

    def __init__(self, vs30_matrix, soil_values, space_dimensions):
        """ Saves a matrix of the velocity below 30 meters of the ground,
        a function for soil values, and the dimensions of the space.

        :param vs30_matrix: TODO
        :param soil_values: TODO
        :param space_dimensions: TODO
        """
        self.space_dimensions = space_dimensions
        self.vs30_matrix = vs30_matrix
        self.soil_values = soil_values # -0.32km

    def assign_soil_to_points(self, physical_network):
        """ Saves soil data associated to each node of physical_network.

        :param physical_network: igraph.Graph
            original physical network
        :return: igraph.Graph
            physical network after adding soil information
        """
        space_x = self.space_dimensions[0]
        space_y = self.space_dimensions[1]
        vs30_matrix_y_length = len(self.vs30_matrix)
        y_step = space_y/vs30_matrix_y_length

        for node in physical_network.vs:
            x = node["x_coordinate"]
            y = node["y_coordinate"]
            # find y-axis bucket
            y_bucket = int(y//y_step)
            # find x bucket
            x_len = len(self.vs30_matrix[y_bucket])
            x_step = space_x/x_len
            x_bucket = int(x//x_step)
            vs30_value = self.vs30_matrix[y_bucket][x_bucket]
            node["vs30"] = vs30_value
            node["soil"] = self.soil_values(vs30_value)

        return physical_network

