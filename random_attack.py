from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import random

class PhysicalRandomAttack(AbstractAttack):

    def attack(self, interdependent_graph: ig.InterdependentGraph) -> None:
        # FLAG TODO: check if necessary
        use_increasing_sample = True

        # get current physical nodes
        physical_network = interdependent_graph.get_physical_network()
        physical_nodes = physical_network.vs['name']
        number_of_physical_nodes = len(physical_nodes)

        node_sample = physical_network.vs["name"]

        list_of_nodes_to_attack = []
        gl_list = []
        for i in range(1, number_of_physical_nodes):
            if use_increasing_sample:
                if len(node_sample) > 0:
                    node = (random.sample(node_sample, 1))[0]
                    list_of_nodes_to_attack.append(node)
                    node_sample.remove(node)
                else:
                    last_was_total_destruction = True
            else:
                list_of_nodes_to_attack = random.sample(node_sample, i)
            GL_per_iteration = interdependent_graph.remove_physical_nodes(list_of_nodes_to_attack)
            gl_list.append(GL_per_iteration)

        #TODO: should this return??