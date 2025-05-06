from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import random
import time

class PhysicalRandomAttack(AbstractAttack):

    def attack(self, interdependent_graph: ig.InterdependentGraph):
        # get current physical nodes
        physical_network = interdependent_graph.get_physical_network()
        physical_nodes = physical_network.vs['name']
        number_of_physical_nodes = len(physical_nodes)

        # establish sample to draw nodes from
        node_sample = physical_network.vs["name"]

        # gl values will be stored in a list
        gl_list = []
        # physical nodes lost after each removal
        physical_nodes_lost = []
        # logical nodes lost after each removal
        logical_nodes_lost = []

        # start loop to remove physical nodes one by one
        for i in range(1, number_of_physical_nodes):
            # add a node to the list of nodes to attack and remove
            # it from the sample
            picked_node_index = random.randrange(0, len(node_sample))
            node = node_sample.pop(picked_node_index)

            # obtain and save GL
            gl_per_iteration = interdependent_graph.remove_physical_nodes([node])

            gl_list.append(gl_per_iteration)

            # obtain physical nodes lost
            physical_nodes_lost.append(interdependent_graph.get_lost_physical_nodes())

            # obtain logical nodes lost
            logical_nodes_lost.append(interdependent_graph.get_lost_logical_nodes())

        # reset variables associated to the network state during the
        # cascading failure
        interdependent_graph.reset_cascading_failure_state()

        return gl_list, physical_nodes_lost, logical_nodes_lost