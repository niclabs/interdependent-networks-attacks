""" Recurrent funtions to process csv data

This script contains functions to read data from .csv files that contain
information regarding networks, in particular interdependent networks.

To properly function the igraph library must be available, as well as csv.

This file can also be imported as a module and contains the following
functions:
    * get_different_nodes - returns a list with the different node names
    * set_graph_from_csv - returns an igraph graph created with the data
    * get_list_of_coordinates_from_csv - returns dictionary with the
    coordinates associated to each node (for physically embbeded networks)
"""
import csv
import igraph

def get_different_nodes(csv_file):
    """Gets the different node names contained in the .csv file

    :param csv_file: str
        string containing the complete file path to the .csv file to read.
        The expected format is a list of edges as "node1,node2", where the
        first character of the node name indicates the node type. Nodes
        can be physical (start with a 'p') or logical ('l')
    :return: list
        a list with all the different node names in the .csv file
    """
    node_dict = {}
    node_dict_aux = {}
    interlink_flag = False
    with open(csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar=',')
        for row in reader:
            #if the node names start with different characters the edge is
            #an interlink
            if row[0][0] != row[1][0]:
                interlink_flag = True
            # for interlinks we use different sets
            if interlink_flag:
                node_dict[row[0]] = ""
                node_dict_aux[row[1]] = ""
            #otherwise the same set is used
            else:
                node_dict[row[0]] = ""
                node_dict[row[1]] = ""
    node_names = []
    # node names are transformed to lists accordingly
    if interlink_flag:
        node_names = list(node_dict.keys()) + list(node_dict_aux.keys())
    else:
        prefix_name = list(node_dict.keys())[0][0]
        for k in range(len(node_dict.keys())):
            node_names.append("{}{}".format(prefix_name, k))
    return node_names

def set_graph_from_csv(csv_file, graph=None):
    if graph is None:
        nodes_names = get_different_nodes(csv_file)
        graph = igraph.Graph(len(nodes_names))
        graph.vs['name'] = nodes_names

    with open(csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar=',')
        for row in reader:
            first = row[0]
            second = row[1]
            graph.add_edge(first, second)
    return graph

def get_list_of_coordinates_from_csv(csv_file):
    coord_dict = {}

    with open(csv_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar=',')
        for row in reader:
            x = float(row[1])
            y = float(row[2])
            coord_dict[row[0]] = [x, y]

    return coord_dict