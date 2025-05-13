from __future__ import annotations

from typing_extensions import override
import seismic_data.image_process as ip
import seismic_data.seismic_data_processor as sdp
import seismic_data.map_handler as mp
from lapf import ProbabilisticLocalizedAttack
import random
import numpy

class SeismicAttack(ProbabilisticLocalizedAttack):

    space_dimensions = (0, 0)
    seismic_data_file = ""

    @staticmethod
    @override
    def get_results_dict(g_l, physical_nodes_removed, logical_nodes_removed, params):
        """ Returns the shape in which the results will be saved.

        :param g_l: list
            gl values obtained per cascading failure iteration
        :param physical_nodes_removed: list
            names of physical nodes removed
        :param logical_nodes_removed: list
            names of logical nodes removed
        :param params: dict
            other parameters
        :return: dict
            contains information to be added in results
        """
        res_dict = {"GL": g_l,
                    "pnodes_removed": physical_nodes_removed,
                    "lnodes_removed": logical_nodes_removed,
                    "magnitude": params["magnitude"],
                    "depth": params["depth"],
                    "event_type": params["event_type"]}
        return res_dict

    @override
    def setup_network(self):
        """ This function prepares the interdependent network to be used
        in the attack by adding local properties to each node as needed.

        This function extends the one defined in ProbabilisticLocalizedAttacks.

        Sets soil values associated to each node within the
        InterdependentNetwork object associated to the SeismicAttack,
        and sets the data containing the parameters to be used during the
        attack method.

        :return: None
        """
        # get physical network
        physical_net = self.interdependent_network.get_physical_network()
        # get vss30
        vs30_matrix = ip.create_values_matrix('seismic_data/m_full_map.png', 'seismic_data/map_scale2.png', 2200, 0)
        # make map
        map_obj = mp.SoilMap(vs30_matrix, sdp.soil_value, self.space_dimensions)
        # set soil things onto physical network
        physical_net = map_obj.assign_soil_to_points(physical_net)
        # re-set modified physical network
        self.interdependent_network.set_physical_network(physical_net)

        # set data parameters for the attack
        seismic_data = sdp.load_seismic_data_from_file(self.seismic_data_file)
        data = []
        for center in self.centers:
            for params in seismic_data:
                new_param = {"epicenter": center}
                new_param.update(params)
                data.append(new_param)
        # save data parameters
        self.data = data

    def set_space_dimensions(self, x_coordinate, y_coordinate):
        self.space_dimensions = (x_coordinate, y_coordinate)

    def set_seismic_data_file(self, file_path):
        self.seismic_data_file = file_path

    @staticmethod
    def seismic_probability_function_chile(vertex, params, mode="linear"):
        """ Probability function to be used for seismic attacks.

        TODO: set failure probability function as variable

        :param vertex: igraph.Vertex
            igraph object for vertex that contains local info associated
            to the node
        :param params: dict
            required parameter to determine failure probability of the vertex
        :param mode: str
            used to determine which function will be used to obtain the
            probability of failure (will be refactored)
        :return: boolean
            represents whether the vertex fails or not
        """
        # TODO: fix debugging code and functions for failure probability
        vertex_x = vertex["x_coordinate"]
        vertex_y = vertex["y_coordinate"]
        epicenter_x = params["epicenter"][0]
        epicenter_y = params["epicenter"][1]
        R_c = numpy.sqrt(((vertex_x - epicenter_x) ** 2) + ((vertex_y - epicenter_y) ** 2))
        R = sdp.coordinates_to_km_chile(R_c)
        St_t = vertex["soil"]
        Vs30 = vertex["vs30"]
        Mw = params["magnitude"]
        H = params["depth"]
        Feve = params["event_type"]

        pga_value = sdp.get_chile_pga2(Mw, H, Feve, R, St_t, Vs30)  # (Mw, H, Feve, R, St_t, Vs30)
        # DEBUG
        debug = False
        if debug:
            print("------------- Feve: {}".format(Feve))
            aux_Mw = 0.8
            pga_list = {}
            while aux_Mw < 10:
                aux_pga = sdp.get_chile_pga2(aux_Mw, H, Feve, R, St_t, Vs30)
                pga_list[aux_Mw] = aux_pga
                if aux_Mw < 1:
                    print("Mw {}, pga ratio: {}, pga {}".format(round(aux_Mw, 1), 1, round(pga_list[aux_Mw] * 10 ** 9, 1)))
                else:
                    print("Mw {}, pga ratio: {}, pga {}".format(round(aux_Mw, 1), round(pga_list[aux_Mw] / pga_list[round(aux_Mw - 1, 1)], 1), round(pga_list[aux_Mw] * 10 ** 9, 1)))
                aux_Mw += 1
            print("-------------")

        # Usar SHINDO scale para las probabilidades
        # notar que la escala no va a ser lineal
        if mode == "linear":
            failure_probability = sdp.linear_shindo_scale_probability(pga_value)
        else:
            failure_probability = sdp.shindo_scale_probability(pga_value)

        return random.uniform(0, 1) <= failure_probability

