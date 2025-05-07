from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import numpy

class LocalizedAttack(AbstractAttack):

    def __init__(self):
        self.centers = []
        self.radii = []

    def attack(self, interdependent_graph: ig.InterdependentGraph):
        """ Returns a dict with complete data regarding the localized
        attacks to be simulated.

        The centers and radii data for each attack must be provided using
        functions provided by the LocalizedAttack class.

        :param interdependent_graph: InterdependentGraph
            system to be attacked
        :return: list
            Contains a list of dictionaries where each dict contains the
            following keys: "x_center", "y_center", "radius", "GL", "pnodes_removed", "lnodes_removed"
        """
        results = []
        physical_network = interdependent_graph.get_physical_network()

        # get results for each center and radii
        for center in self.centers:
            x_center = center[0]
            y_center = center[1]
            for radius in self.radii:
                # Get nodes to attack
                nodes_to_attack = []  # name list
                # determine nodes within the targeted area
                for vertex in physical_network.vs:
                    x = vertex["x_coordinate"]
                    y = vertex["y_coordinate"]
                    if ((x - x_center) ** 2) + ((y - y_center) ** 2) <= radius ** 2:
                        nodes_to_attack.append(vertex["name"])

                # obtain and save GL
                gl_per_iteration = interdependent_graph.remove_physical_nodes(nodes_to_attack)

                # save results
                result_dict = {"x_center": x_center,
                               "y_center": y_center,
                               "radius": radius,
                               "GL": gl_per_iteration,
                               "pnodes_removed": nodes_to_attack,
                               "lnodes_removed": interdependent_graph.get_lost_logical_nodes()}
                results.append(result_dict)
                
                # reset variables associated to the network state during the
                # cascading failure
                interdependent_graph.reset_cascading_failure_state()

        return results

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

    def set_radii(self, radii_list):
        """ Saves the radii to be tested during a localized attack
        simulation.

        :param radii_list: list
            contains radii to be tested
        :return: None
        """
        self.radii = radii_list

    def set_centers(self, center_list):
        """ Saves the centers to be tested from center_list.

        :param center_list: list
            contains centers, each center is a tuple
        :return: None
        """
        self.centers = center_list