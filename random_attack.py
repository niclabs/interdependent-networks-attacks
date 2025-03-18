from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import random

class PhysicalRandomAttack(AbstractAttack):

    def attack(self, interdependent_graph: ig.InterdependentGraph):
        # FLAG TODO: check if necessary
        use_increasing_sample = True

        # get current physical nodes
        physical_network = interdependent_graph.get_physical_network()
        physical_nodes = physical_network.vs['name']
        number_of_physical_nodes = len(physical_nodes)

        # establish sample to draw nodes from
        node_sample = physical_network.vs["name"]

        # assign initial list of nodes to attack (starts empty)
        list_of_nodes_to_attack = []
        # gl values will be stored in a list
        gl_list = []

        # start loop to remove physical nodes one by one
        for i in range(1, number_of_physical_nodes):
            if use_increasing_sample:
                if len(node_sample) > 0:
                    # add a node to the list of nodes to attack and remove
                    # it from the sample
                    picked_node_index = random.randrange(0,len(node_sample))
                    node = node_sample.pop(picked_node_index)
                    list_of_nodes_to_attack.append(node)
                else:
                    last_was_total_destruction = True
            else:
                list_of_nodes_to_attack = random.sample(node_sample, i)
            GL_per_iteration = interdependent_graph.remove_physical_nodes(list_of_nodes_to_attack)
            print(GL_per_iteration)
            gl_list.append(GL_per_iteration)

        #TODO: should this return??