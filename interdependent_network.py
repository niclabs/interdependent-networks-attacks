""" Class to process and manage interdependent networks

Tha class InterdependentGraph manages the creation and setup of
interdependent networks. It also manages node deletion or attack and their
subsequent cascading failures.

To attack an InterdependentNetwork object using different attack
strategies, an AbstractAttack object must be used (double dispatch)

To properly function the igraph library must be available, as well as csv.
"""
from __future__ import annotations
import igraph
import csv
import csv_utils
import numpy
from abstract_attack import AbstractAttack


class InterdependentGraph(object):

    def __init__(self):
        """ InterdependentGraph constructor

        The constructor creates an empty InterdependentGraph object as it
        must be properly set up afterward.
        """
        self.interactions_network = None
        self.logical_network = None
        self.physical_network = None
        self.logical_providers = None
        self.physical_providers = None
        self.initial_number_of_functional_logical_nodes = -1
        self.current_number_of_functional_logical_nodes = -1
        self.physical_rosetta = dict()
        self.inverse_physical_rosetta = dict()
        self.logical_rosetta = dict()
        self.inverse_logical_rosetta = dict()
        self.inter_rosetta_physical = dict()
        self.inter_rosetta_logical = dict()
        self.inner_inter_rosetta = dict()
        self.current_network_state = dict()
        self.physical_nodes_lost = []
        self.logical_nodes_lost = []
        self.in_cascading_failure = False

    def reset_cascading_failure_state(self):
        self.current_network_state = self._initialize_network_state()
        self.in_cascading_failure = False

    def _initialize_network_state(self):
        n_phys_nodes = len(self.physical_network.vs['name'])
        n_logic_nodes = len(self.logical_network.vs['name'])
        n_inter_nodes = len(self.interactions_network.vs['name'])
        network_state_dict = {"phys_input": [True for i in range(n_phys_nodes)],
                              "logic_input": [True for i in range(n_logic_nodes)],
                              "inter_input": [True for i in range(n_inter_nodes)]}
        return network_state_dict

    def _get_nodes_lost(self, mode):
        node_list = []
        if mode == "phys_input":
            inverse_rosetta = self.inverse_physical_rosetta
        else:
            inverse_rosetta = self.inverse_logical_rosetta

        phys_input = self.current_network_state[mode]
        for i in range(len(phys_input)):
            if not phys_input[i]:
                node_list.append(inverse_rosetta[i])
        return node_list

    def get_lost_physical_nodes(self):
        return self._get_nodes_lost("phys_input")

    def get_lost_logical_nodes(self):
        return self._get_nodes_lost("logic_input")

    def create_from_csv(self, logical_network_csv_file_path, physical_network_csv_file_path, interactions_network_csv_file_path, pnodes_data, providers_csv="",
                        logical_provider_nodes=(), physical_provider_nodes=()):
        """Fills an InterdependentGraph object using .csv files

        :param logical_network_csv_file_path: str
            string containing the complete file path to the .csv that
            contains the logical network structure. The expected format is
            a list of edges as "node1,node2", where the first character is
            an 'l'.
        :param physical_network_csv_file_path: str
            string containing the complete file path to the .csv that
            contains the physical network structure. The expected format
            is a list of edges as "node1,node2", where the first character
            is an 'l'.
        :param interactions_network_csv_file_path:
            string containing the complete file path to the .csv file that
            contains the interlinks between the physical and logical
            network. The expected format is a list of edges as
            "node1,node2", where the first character can be either 'p' or
            'l'.
        :param pnodes_data: str
            string containing the complete file path to the .csv that
            contains the physical node names associated to their
            coordinates in space.
        :param providers_csv: str
            string containing the complete file path to the .csv that
            contains the logical and physical nodes considered to be
            provider nodes.

            Can default to the empty string
        :param logical_provider_nodes: tuple
            tuple containing the names of the logical provider nodes.
            Should be used only if providers_csv is an empy str.
        :param physical_provider_nodes: tuple
            tuple containing the names of the physical provider nodes.
            Should be used only if providers_csv is an empy str.
        """
        x = 0
        y = 1
        # Create logical network from csv file
        self.logical_network = csv_utils.set_graph_from_csv(logical_network_csv_file_path)

        # Create physical network from csv file
        self.physical_network = csv_utils.set_graph_from_csv(physical_network_csv_file_path)
        coord_dict = csv_utils.get_list_of_coordinates_from_csv(pnodes_data)
        x_positions = []
        y_positions = []
        for i in range(len(self.physical_network.vs)):
            node_name = self.physical_network.vs[i]['name']
            x_positions.append(coord_dict[node_name][x])
            y_positions.append(coord_dict[node_name][y])

        self.physical_network.vs['x_coordinate'] = x_positions
        self.physical_network.vs['y_coordinate'] = y_positions

        # Create interactions graph from csv file. This contains the nodes of both networks
        self.interactions_network = csv_utils.set_graph_from_csv(interactions_network_csv_file_path)

        # set providers from file
        # TODO: check if providers_csv should continue to be "optional"
        if providers_csv != "":
            logical_provider_nodes = []
            physical_provider_nodes = []
            with open(providers_csv, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar=',')
                type_of_provider = ""
                for row in reader:
                    if row[0] == "logic":
                        type_of_provider = "logic"
                    elif row[0] == "physical":
                        type_of_provider = "physical"
                    else:
                        if type_of_provider == "logic":
                            logical_provider_nodes.append(str(row[0]))
                        if type_of_provider == "physical":
                            physical_provider_nodes.append(str(row[0]))

        logical_network_name_list = self.logical_network.vs['name']
        physical_net_name_list = self.physical_network.vs['name']
        type_list = []
        for node in self.interactions_network.vs:
            if node['name'] in logical_network_name_list:
                type_list.append(0)
            elif node['name'] in physical_net_name_list:
                type_list.append(1)
        self.interactions_network.vs['type'] = type_list

        # save provider nodes
        self.logical_providers = logical_provider_nodes
        self.physical_providers = physical_provider_nodes

        # save initial set of functional logical nodes
        # TODO: This should count nodes with a path to a provider. The following is true only if the network has one connected component
        self.initial_number_of_functional_logical_nodes = \
            len([a for a in self.logical_network.vs if self.logical_network.degree(a.index) > 0])

        self._set_rosettas()
        self.reset_cascading_failure_state()

    def get_logical_network(self):
        """Returns the logical network of the InterdependentGraph object

        :return: igraph.Graph
        """
        return self.logical_network

    def add_edges_to_physical_network(self, edge_tuple_array):
        """Function to add physical links or edges

        :param edge_tuple_array: list
            corresponds to a list of size 2 tuples. Each tuple represents
            a new physical link to be added.
        """
        self.physical_network.add_edges(edge_tuple_array)

    def get_logical_providers(self):
        """ Returns list of logical provider nodes

        :return: list
        """
        return self.logical_providers

    def get_physical_network(self):
        """ Returns the physical network of the InterdependentGraph object

        :return: igraph.Graph
        """
        return self.physical_network

    def get_physical_providers(self):
        """Returns list of physical provider nodes

        :return: list
        """
        return self.physical_providers

    def get_interlinks(self):
        """ Returns the interlinks network of the InterdependentGraph

        :return: igraph.Graph
        """
        return self.interactions_network

    def set_logical_network(self, logical_network: igraph.Graph):
        """ Assigns an existing logical network to the InterdependentGraph

        :param logical_network: igraph.Graph
            contains a logical network with all the expected data
        """
        self.logical_network = logical_network

    def set_physical_network(self, physical_network):
        """ Assigns an existing physical network to the current object

        :param physical_network: igraph.Graph
            contains a physical network with all the expected data
        """
        self.physical_network = physical_network

    def set_interlinks(self, interlinks_network):
        """ Assigns an existing interlinks network to the current object

        :param interlinks_network:
            contains an interlinks network with all the expected data
        """
        self.interactions_network = interlinks_network

    @staticmethod
    def _get_rosetta_from_network(network: igraph.Graph):
        """Generates a dictionary to assign a number to each network node

        This staticmethod is meant for internal use only. It associates a
        number to each node present at the current state of the network
        received. The objective is to keep track of nodes as they are
        eliminated after an attack. Although igraph assigns an index to
        each node, once a node is deleted, the indices are adjusted so
        only consecutive numbers are considered. This means that a node
        index could change within the igraph.Graph object once another
        node is deleted.

        :param network: igraph.Graph
            must contain a network where each node has an assigned name
        :return: dict
            dictionary associating each node name to a number
        """
        roseta = {}
        for i in range(len(network.vs)):
            node_name = network.vs[i]['name']
            roseta[node_name] = i
        return roseta

    def _set_inter_rosettas(self):
        name_by_index = []
        roseta_phys = {}
        roseta_logic = {}
        for i in range(len(self.interactions_network.vs)):
            node_name = self.interactions_network.vs[i]['name']
            name_by_index.append(node_name)
            if 'l' in node_name:
                roseta_logic[node_name] = self.logical_network.vs['name'].index(node_name)
            else:
                roseta_phys[node_name] = self.physical_network.vs['name'].index(node_name)
        self.inter_rosetta_logical = roseta_logic
        self.inter_rosetta_physical = roseta_phys
        self.inter_name_by_index = name_by_index

    def _set_rosettas(self):
        """Set translation rosettas for each network

        This method is meant for internal use only.
        """
        self.physical_rosetta = self._get_rosetta_from_network(self.physical_network)
        self.inverse_physical_rosetta = dict([(v, [k for k, v1 in self.physical_rosetta.items() if v1 == v][0])
                                for v in set(self.physical_rosetta.values())])
        self.logical_rosetta = self._get_rosetta_from_network(self.logical_network)
        self.inverse_logical_rosetta = dict([(v, [k for k, v1 in self.logical_rosetta.items() if v1 == v][0])
                                              for v in set(self.logical_rosetta.values())])
        self.inner_inter_rosetta = self._get_rosetta_from_network(self.interactions_network)
        self._set_inter_rosettas()

    def create_from_graphs(self, logical_graph: igraph.Graph, logical_provider_nodes: list, physical_graph: igraph.Graph, physical_provider_nodes: list,
                           interactions_graph: igraph.Graph):
        """Creates an InterdependentGraph object from igraph.Graph objects

        :param logical_graph: igraph.Graph
            contains the logical network
        :param logical_provider_nodes: list
            contains the names of logical provider nodes
        :param physical_graph: igraph.Graph
            contains the physical network
        :param physical_provider_nodes: list
            contains the names of physical provider nodes
        :param interactions_graph: igraph.Graph
            contains the interlinks graph
        """

        # save logical graph (create copy from original)
        self.logical_network = igraph.Graph([e.tuple for e in logical_graph.es])
        self.logical_network.vs["name"] = logical_graph.vs["name"]

        # save physical graph (create copy from original)
        self.physical_network = igraph.Graph([e.tuple for e in physical_graph.es])
        self.physical_network.vs["name"] = physical_graph.vs["name"]
        self.physical_network.vs["x_coordinate"] = physical_graph.vs["x_coordinate"]
        self.physical_network.vs["y_coordinate"] = physical_graph.vs["y_coordinate"]

        # prepare and save interactions graph
        self.interactions_network = igraph.Graph([e.tuple for e in interactions_graph.es])
        self.interactions_network.vs["name"] = interactions_graph.vs["name"]
        as_net_name_list = self.logical_network.vs["name"]
        physical_net_name_list = self.physical_network.vs["name"]
        type_list = []
        for node in self.interactions_network.vs:
            if node['name'] in as_net_name_list:
                type_list.append(0)
            elif node['name'] in physical_net_name_list:
                type_list.append(1)
        self.interactions_network.vs['type'] = type_list

        # save provider nodes
        self.logical_providers = logical_provider_nodes
        self.physical_providers = physical_provider_nodes

        # save initial set of functional nodes
        self.initial_number_of_functional_logical_nodes = \
            len([a for a in self.logical_network.vs if self.logical_network.degree(a.index) > 0])

        self._set_rosettas()
        self.reset_cascading_failure_state()
        return self


    def remove_physical_nodes(self, nodes_to_delete):
        """Removes the specified nodes and simulates the cascading failure

        This function handles the effect of removing a set of nodes from
        the InterdependentGraph. To do so, it simulates the resulting
        cascading failure until the system fully stabilizes.

        :param nodes_to_delete: list
            contains the names of the nodes to be deleted
        :return gl_per_iteration: list
            contains the GL value of each iteration of the cascading
            failure triggered by the removal of the nodes in
            nodes_to_delete. The length of the list corresponds to the
            Number Of Iterations or NOI measure.
        """
        # get number of nodes in each network
        n_phys_nodes = len(self.physical_network.vs['name'])
        n_logic_nodes = len(self.logical_network.vs['name'])
        n_inter_nodes = len(self.interactions_network.vs['name'])

        # we also track the G_L associated to each iteration
        gl_per_iteration = []

        # We represent the state of each node in each network as True if
        #the node is alive, and False if it is no longer functional
        # The system starts with all nodes alive
        phys_input = self.current_network_state["phys_input"]
        logic_input = self.current_network_state["logic_input"]
        inter_input = self.current_network_state["inter_input"]

        # these nodes will be removed from each network
        phys_nodes_to_delete = []
        logic_nodes_to_delete = []

        # using the network state saved the nodes to be removed
        # are updated.
        physical_nodes_lost_in_previous_state = self.get_lost_physical_nodes()

        nodes_to_delete_aux = list(set(nodes_to_delete).union(set(physical_nodes_lost_in_previous_state)))
        for pnode_name in nodes_to_delete_aux:
            phys_nodes_to_delete.append(self.physical_rosetta[pnode_name])
        phys_nodes_to_delete.sort()

        # then logic nodes are considered. These may come from a previous iteration
        for lnode_name in self.get_lost_logical_nodes():
            logic_nodes_to_delete.append(self.logical_rosetta[lnode_name])

        # physical nodes to be deleted in the current iteration
        current_phys_nodes_to_delete = []
        # logical nodes to be deleted in the current iteration
        current_logic_nodes_to_delete = []

        # Set the nodes to delete in the physical network as removed
        for node_name in nodes_to_delete:
            phys_input[self.physical_rosetta[node_name]] = False

        while True:
            # if there are no more nodes to delete, i.e, the network has
            #stabilized, then stop
            if phys_nodes_to_delete == current_phys_nodes_to_delete and logic_nodes_to_delete == current_logic_nodes_to_delete:
                break

            # update the nodes to be deleted in this iteration
            if current_phys_nodes_to_delete != []:
                phys_nodes_to_delete = current_phys_nodes_to_delete.copy()
            if current_logic_nodes_to_delete != []:
                logic_nodes_to_delete = current_logic_nodes_to_delete.copy()

            # Delete the nodes to delete on each network, including the interactions network
            for pnode in phys_nodes_to_delete:
                phys_input[pnode] = False

            for lnode in logic_nodes_to_delete:
                logic_input[lnode] = False

            # interactions network
            for inode in range(n_inter_nodes):
                inode_name = self.inter_name_by_index[inode]
                if inode_name in self.inter_rosetta_logical.keys():
                    l_index = self.inter_rosetta_logical[inode_name]
                    inter_input[inode] = logic_input[l_index]
                else:
                    p_index = self.inter_rosetta_physical[inode_name]
                    inter_input[inode] = phys_input[p_index]

            # Determine all nodes that fail because they don't have connection to a provider
            ## 1.- physical
            while True:
                phys_input_old = phys_input.copy()
                phys_input = self._get_physical_nodes_lost_by_cc(phys_input)
                if phys_input_old == phys_input:
                    del phys_input_old
                    break
            ## 2.-logical
            while True:
                logic_input_old = logic_input.copy()
                if self.logical_network.is_directed():
                    # TODO
                    pass
                    #logic_input = get_nodes_lost_directed_graph(logic_graph, logic_input, logic_providers, logic_roseta)
                else:
                    logic_input = self._get_logical_nodes_lost_by_cc(logic_input)

                if logic_input == logic_input_old:
                    del logic_input_old
                    break

            ## 3.- interlink
            while True:
                inter_input_old = inter_input.copy()
                inter_input = self._remove_isolated_nodes_from_inter(inter_input)
                if inter_input == inter_input_old:
                    del inter_input_old
                    break

            # update lists of nodes lost
            # Add them to the nodes to delete on the next iteration
            current_phys_nodes_to_delete_set = set()
            current_logic_nodes_to_delete_set = set()

            for pnode in range(n_phys_nodes):
                if not phys_input[pnode]:
                    current_phys_nodes_to_delete_set.add(pnode)

            for lnode in range(n_logic_nodes):
                if not logic_input[lnode]:
                    current_logic_nodes_to_delete_set.add(lnode)

            for inode in range(n_inter_nodes):
                if not inter_input[inode]:
                    inode_name = self.inter_name_by_index[inode]
                    if inode_name in self.inter_rosetta_logical.keys():
                        l_index = self.inter_rosetta_logical[inode_name]
                        current_logic_nodes_to_delete_set.add(l_index)
                    else:
                        p_index = self.inter_rosetta_physical[inode_name]
                        current_phys_nodes_to_delete_set.add(p_index)

            current_phys_nodes_to_delete = list(current_phys_nodes_to_delete_set)
            current_phys_nodes_to_delete.sort()
            current_logic_nodes_to_delete = list(current_logic_nodes_to_delete_set)
            current_logic_nodes_to_delete.sort()

            gl_per_iteration.append(numpy.round(1 - len(current_logic_nodes_to_delete) / n_logic_nodes, 4))

        # update state to return it
        self.current_network_state["phys_input"] = phys_input.copy()
        self.current_network_state["logic_input"] = logic_input.copy()
        self.current_network_state["inter_input"] = inter_input.copy()

        return gl_per_iteration

    @staticmethod
    def _get_nodes_lost_by_cc(network, list_input, providers, rosetta):
        """ Modifies the contents of list_input to reflect the nodes that
        have been lost.

        The list list_input contains booleans associated to the node index
        of each node in network. True signifies that the node is still
        functional, and False that it is not.

        :param network: igraph.Graph
        :param list_input: list
            contains booleans
        :param providers: list
            contains provider nodes
        :param rosetta: dict
            allows for translation between node names and index
        :return: list
            updated version of list_input
        """
        new_lost_nodes = []
        network_copy = network.copy()
        input_copy = list_input.copy()
        nodes_to_delete = [i for i in range(len(list_input)) if not list_input[i]]

        network_copy.delete_vertices(nodes_to_delete)
        clusters = network_copy.clusters()
        for c in clusters:
            is_alive = False
            name_c = network_copy.vs[c]['name']
            if len(name_c) > len(providers):
                for sup in providers:
                    if sup in name_c:
                        is_alive = True
                        break
            elif len(name_c) > 1:
                for node in name_c:
                    if node in providers:
                        is_alive = True
                        break
            else:
                is_alive = False
            if not is_alive:
                new_lost_nodes = new_lost_nodes + name_c

        del network_copy

        for node in new_lost_nodes:
            index = rosetta[node]
            input_copy[index] = False

        return input_copy

    def _get_physical_nodes_lost_by_cc(self, phys_input):
        """ Modifies the contents of phys_input to reflect the nodes that
        have been lost in the physical network.

        The list phys_input contains booleans associated to the node index
        of each node in the physical network. True signifies that the node
        is still functional, and False that it is not.

        :param phys_input: list
            contains booleans
        :return: list
            updated version of list_input
        """
        return self._get_nodes_lost_by_cc(self.physical_network, phys_input, self.physical_providers, self.physical_rosetta)

    def _get_logical_nodes_lost_by_cc(self, logic_input):
        """ Modifies the contents of logic_input to reflect the nodes that
        have been lost in the logical network.

        The list logic_input contains booleans associated to the node index
        of each node in the logical network. True signifies that the node
        is still functional, and False that it is not.

        :param logic_input: list
            contains booleans
        :return: list
            updated version of list_input
        """
        return self._get_nodes_lost_by_cc(self.logical_network, logic_input, self.logical_providers, self.logical_rosetta)

    def _remove_isolated_nodes_from_inter(self, inter_input):
        """ Modifies the contents of inter_input to reflect the nodes that
        have been lost in the interlinks network.

        The list inter_input contains booleans associated to the node index
        of each node in the logical network. True signifies that the node
        is still functional, and False that it is not.

        :param inter_input: list
            contains booleans
        :return: list
            updated version of list_input
        """
        new_lost_nodes = []
        inter_graph_copy = self.interactions_network.copy()
        inter_input_copy = inter_input.copy()
        nodes_to_delete = [i for i in range(len(inter_input)) if not inter_input[i]]

        inter_graph_copy.delete_vertices(nodes_to_delete)
        clusters = inter_graph_copy.clusters()
        for c in clusters:
            named_c = inter_graph_copy.vs[c]['name']
            if len(named_c) < 2:
                new_lost_nodes = new_lost_nodes + named_c

        del inter_graph_copy

        for node in new_lost_nodes:
            index = self.inner_inter_rosetta[node]
            inter_input_copy[index] = False

        return inter_input_copy

    def get_ratio_of_functional_logical_nodes(self):
        """Returns the current rate of functional logical nodes or G_L

        :return: float
            ratio of current functional logical nodes
        """
        return self.current_number_of_functional_logical_nodes / self.initial_number_of_functional_logical_nodes

    def attack(self, attack_strategy: AbstractAttack):
        return attack_strategy.attack(self)