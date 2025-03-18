""" Abstract class to manage the nodes removed by an attack

The class AbstractAttack is an abstract class mean to provide for a
template for every type of attack to be performed over an
InterdependentGraph object.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import interdependent_network as ig

class AbstractAttack(ABC):
    @abstractmethod
    def attack(self, interdependent_graph: ig.InterdependentGraph):
        pass