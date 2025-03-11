""" Abstract class to manage the nodes removed by an attack

The class AbstractAttack is an abstract class mean to provide for a
template for every type of attack to be performed over an
InterdependentGraph object.
"""

from abc import ABC, abstractmethod
from interdependent_network import InterdependentGraph

class AbstractAttack(ABC):
    @abstractmethod
    def attack_interdependent_network(self, interdependent_network: InterdependentGraph):
        pass