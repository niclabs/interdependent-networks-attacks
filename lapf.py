from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import numpy

class ProbabilisticLocalizedAttack(AbstractAttack):

    def __init__(self):
        self.data = None
        self.probability_function = None
        self.interdependent_network = None
        self.centers = []

    def attack(self, interdependent_graph: ig.InterdependentGraph):
        # save interdependent network for setup
        self.interdependent_network = interdependent_graph
        # setup network as specified
        self.setup_network()
        results = []
        physical_network = interdependent_graph.get_physical_network()
        # perform attacks according to the parameters in data
        for param in self.data:
            # Get nodes to attack
            nodes_to_attack = []  # name list
            # determine nodes within the targeted area
            for vertex in physical_network.vs:
                if self.probability_function(vertex, param):
                    nodes_to_attack.append(vertex["name"])

            # obtain and save GL
            gl_per_iteration = interdependent_graph.remove_physical_nodes(nodes_to_attack)

            # save results
            result_dict = self.get_results_dict(gl_per_iteration, nodes_to_attack, interdependent_graph.get_lost_logical_nodes(), param)
            results.append(result_dict)

            # reset variables associated to the network state during the
            # cascading failure
            interdependent_graph.reset_cascading_failure_state()
        return results

    def set_data(self, data):
        self.data = data

    def set_probability_function(self, probability_function):
        self.probability_function = probability_function

    def setup_network(self):
        """ This function prepares the interdependent network to be used
        in the attack by adding local properties to each node as needed.

        This function can be extended if necessary.

        :return:
        """
        pass

    @staticmethod
    def get_results_dict(g_l, physical_nodes_removed, logical_nodes_removed, params):
        """ Returns the shape in which the results will be saved.

        :param g_l: list
            gl values obtained per cascading failure iteration
        :param physical_nodes_removed: list
            names of physical nodes removed
        :param logical_nodes_removed: list
            names of logical nodes removed
        :param params: dict
            other parameters
        :return: dict
            contains information to be added in results
        """
        return {"GL": g_l, "pnodes_removed": physical_nodes_removed, "lnodes_removed": logical_nodes_removed}

    def set_centers(self, center_list):
        """ Saves the centers to be tested from center_list.

        :param center_list: list
            contains centers, each center is a tuple
        :return: None
        """
        self.centers = center_list

    def set_centers_uniformly(self, x_coordinate, y_coordinate, number_of_centers):
        """ Generates center list to simulate localized attacks.

        :param x_coordinate: int
            size of the space in the x-axis
        :param y_coordinate: int
            size of the space in the y-axis
        :param number_of_centers: int
        :return: None
        """
        self.centers = []
        # get the space area
        area = x_coordinate * y_coordinate
        # the space will be divided into "squares" or "cells"
        square_side = int(numpy.sqrt(area / number_of_centers))
        width_cells = int(x_coordinate / square_side)
        length_cells = int(y_coordinate / square_side)

        # within each cell we obtain a center
        for i in range(width_cells):
            x_center = (i + 0.5) * square_side
            for j in range(length_cells):
                y_center = (j + 0.5) * square_side
                self.centers.append((x_center, y_center))
