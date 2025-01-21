""" Class to process and manage interdependent networks

Tha class InterdependentGraph manages the creation and setup of
interdependent networks. It also manages node deletion or attack and their
subsequent cascading failures.

To attack an InterdependentNetwork object using different attack
strategies, an AbstractAttack object must be used as visitor
(visitor pattern).

To properly function the igraph library must be available, as well as csv.
"""
import igraph
import csv
import csv_utils

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
        self.logical_rosetta = dict()
        self.inner_inter_rosetta = dict()

    def create_physical_logical_network_from_csv(self, logical_network_csv_file_path, physical_network_csv_file_path, interactions_network_csv_file_path, pnodes_data, providers_csv="",
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

    def get_logical_network(self):
        return self.logical_network

    def add_edges_to_physical_network(self, edge_tuple_array):
        self.physical_network.add_edges(edge_tuple_array)

    def get_logical_providers(self):
        return self.logical_providers

    def get_physical_network(self):
        return self.physical_network

    def get_physical_providers(self):
        return self.physical_providers

    def get_interlinks(self):
        return self.interactions_network

    def set_logical_network(self, logical_network):
        self.logical_network = logical_network
        return self

    def set_physical_network(self, physical_network):
        self.physical_network = physical_network
        return self

    def set_interlinks(self, interlinks_network):
        self.interactions_network = interlinks_network
        return self

    @staticmethod
    def _get_rosetta_from_network(network):
        roseta = {}
        for i in range(len(network.vs)):
            node_name = network.vs[i]['name']
            roseta[node_name] = i
        return roseta

    def _set_rosettas(self):
        self.physical_rosetta = self._get_rosetta_from_network(self.physical_network)
        self.logical_rosetta = self._get_rosetta_from_network(self.logical_network)
        self.inner_inter_rosetta = self._get_rosetta_from_network(self.interactions_network)

    def create_from_graphs(self, logical_graph: igraph.Graph, logical_provider_nodes, physical_graph: igraph.Graph, physical_provider_nodes,
                           interactions_graph: igraph.Graph):

        # TODO: should suffice using "object.copy()"?
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
        return self

    def remove_nodes(self, nodes_to_delete: [str,str]):
        # TODO: Get code from old tests_library.attack_nodes_test
        pass

    def get_ratio_of_functional_logical_nodes(self):
        return self.current_number_of_functional_logical_nodes / self.initial_number_of_functional_logical_nodes