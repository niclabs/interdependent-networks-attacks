from __future__ import annotations
from abstract_attack import AbstractAttack
import interdependent_network as ig
import random

class RandomAttack(AbstractAttack):

    def attack_interdependent_network(self, interdependent_graph: ig.InterdependentGraph) -> None:
        # get current physical nodes
        logical_network = interdependent_graph.get_physical_network()
        logical_nodes = logical_network.vs['name']
        #TODO: get how to remove each node 