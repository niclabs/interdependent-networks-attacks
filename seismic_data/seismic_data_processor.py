""" This script contains all the functions associated to seismic data
processing.
"""

import csv
import numpy
import os


def soil_value(vs30):
    """ Returns the soil coefficient for a given vs30. Currently hardcoded

    :param vs30: float
        Average shear wave velocity down to 30m depth
    :return: float
        Soil coefficient
    """
    soil_coef = -0.506
    return soil_coef#-0.322


def km_to_coordinates_chile(kms):
    """ Converts kilometers to 'coordinate units' as used in the space in
    which the networks are embedded.

    Units were set using Chile as reference.

    :param kms: float
    :return: float
        coordinates units
    """
    coordinate = 20
    km = 175
    factor = coordinate / km  # "coordinate" per km
    return kms * factor


def coordinates_to_km_chile(coordinates):
    """ Converts 'coordinate units' to kilometers as used in the space in
    which the networks are embedded.

    :param coordinates: float
    :return: float
        kilometers
    """
    coordinate = 20
    kms = 175
    factor = kms/coordinate # kms per unit of "coordinate"
    return coordinates*factor


def get_chile_pga_T03(Mw, H, Feve, R, St_t, Vs30):
    """ Returns the ground acceleration for the given parameters according
    to the ground motion prediction equations presented by Idini et al.
    for the chilean territory. Uses equation for time period T = 0.3s.

    :param Mw: float
        Moment magnitude of the seismic event
    :param H: float
        Hypocentral depth in meters
    :param Feve: int
        Represents whether the event is an interface event (Feve = 0) or
        an intraslab event (Feve = 1)
    :param R: float
        Hypocentral distance in meters
    :param St_t: float
        Site effect coefficient given by the local soil
    :param Vs30: float
        Average shear wave velocity down to 30m depth
    :return: float
        Ground acceleration
    """
    # set coefficients as specified in Idini's work for T=0.3s
    c1 = -3.5422
    c2 = 0.9441
    c3 = -0.84814
    c4 = 0.1
    c5 = -0.00173
    c6 = 5
    c7 = 0.35
    c8 = 0.00428
    c9 = -0.05052
    delta_c1 = 2.2017
    delta_c2 = -0.5412
    delta_c3 = -0.36695
    h0 = 50  # 50 km
    Mr = 5
    Vref = 1530  # 1530 m/s

    # obtain values depending on the event type
    if Feve == 0:
        delta_fm = c9 * (Mw ** 2)
    else:
        delta_fm = delta_c1 + delta_c2 * Mw

    # obtain seismic source contribution
    Ff = c1 + c2 * Mw + c8 * (H - h0) * Feve + delta_fm

    # obtain path contribution
    g = (c3 + c4 * (Mw - Mr) + delta_c3 * Feve)
    R0 = ((1 - Feve) * c6 * 10 ** (c7 * (Mw - Mr)))
    Fd = g * numpy.log10(R + R0) + c5 * R

    # obtain local site effects
    Fs = St_t * numpy.log10((Vs30 + 0.00000000000001) / Vref)

    # get log of the predicted ground acceleration
    log10_pga = Ff + Fd + Fs

    # get ground acceleration
    pga = 10 ** log10_pga
    return pga


def linear_shindo_scale_probability(pga):
    """ Returns the failure probability of a node given the predicted
    ground acceleration it experiences.

    :param pga: float
        predicted ground acceleration of a node
    :return: float
        failure probability (values between 0 and 1)
    """
    print_as_progress_string("using linear_shindo")
    gravity_acceleration = 9.81
    # assign a value for tha 'shindo' scale
    max_ms_pga = 4  # TODO: Why saturates at 4? (I forgor :c )
    linear_function = saturated_two_point_line_eq(max_ms_pga, (0.06, 0.0), (6.0, 1.0))
    return shindo_scale_probability(pga, linear_function)

def shindo_scale_probability(pga, probability_function):
    """ Returns the failure probability of a node given the predicted
    ground acceleration it experiences, and a probability function.

    :param pga: float
        predicted ground acceleration of a node
    :param probability_function: function
        must go between 0 and 1
    :return: float
        failure probability (values between 0 and 1)
    """
    gravity_acceleration = 9.81  # TODO: was pga actual acceleration? why gravity??
    # assign a value for tha 'shindo' scale
    ms_pga = pga * gravity_acceleration

    # assign probability value using a linear equation
    prob_value = probability_function(ms_pga)

    if prob_value < 0:
        prob_value = 0
    elif prob_value > 1:
        prob_value = 1

    return prob_value


def stair_shindo_scale_probability(pga):
    """ Returns the failure probability of a node given the predicted
    ground acceleration it experiences. Here a staircase function is
    used. Between limits a linear function is used.

    :param pga: float
        predicted ground acceleration of a node
    :return: float
        failure probability (values between 0 and 1)
    """
    gravity_acceleration = 9.8
    ms_pga = pga * gravity_acceleration
    tiers = {#"0": (0, 0.008),
             #"1": (0.008, 0.025),
             #"2": (0.025, 0.08),
             #"3": (0.08,0.25),
             "4": [(0.025, 0.80), (0.01, 0.1)], # delta = 0.55 -> 0.8 m/s => 10% damage probability
             "5-": [(0.8, 1.4),(0.1,0.2)], # delta = 0.6 -> 1.4 m/s => 20% damage probability
             "5+": [(1.4, 2.5),(0.2,0.5)], # delta = 1.1 -> 2.5 m/s => 50% damage probability
             "6-": [(2.5, 3.15),(0.5,0.85)], # delta = 0.65 -> 3.15 m/s => 85% damage probability
             "6+": [(3.15, 4),(0.85,1)], #delta = 0.85 -> 4 m/s => 100% damage probability
             "7": [(4, float('inf')),(1,1)]}

    for tier_number in tiers:
        if tiers[tier_number][0][0] <= ms_pga < tiers[tier_number][0][1]:
            point_1 = (tiers[tier_number][0][0],tiers[tier_number][1][0])
            point_2 = (tiers[tier_number][0][1],tiers[tier_number][1][1])
            prob_value = _two_point_line_eq(ms_pga, point_1, point_2)
            return prob_value
    return 0

def load_seismic_data_from_file(seismic_data_file):
    """ Load seismic events from a csv file.

    :param seismic_data_file: str
        file path
    :return: list
        contains dictionaries with the information associated to each
        seismic event
    """
    data_dict = load_seismic_events_from_csv(seismic_data_file)
    seismic_data_list = []
    for event_id in data_dict.keys():
        event = data_dict[event_id][0]
        seismic_event = {"magnitude": event['Magnitude'],
                         "depth": event['Depth'],
                         "event_type": event['Fault Type'],
                         "id": event_id}
        seismic_data_list.append(seismic_event)
    return seismic_data_list


def parse_scientific_notation(number_string):
    numbers = number_string.split("E")
    return float(numbers[0]) * (10 ** float(numbers[1]))


def site_reference(site_type):
    values = {'I': 0, 'II': -0.584, 'III': -0.322, 'IV': -0.109, 'V': -0.095, 'VI': -0.212}
    return values[site_type]


def load_seismic_events_from_csv(csv_file):
    """ Returns a dictionary with the data of each seismic event in
    a csv file containing the information.

    :param csv_file: str
        file path
    :return: dict
    """

    first_row = True
    first_row_dict = {}
    data_dict = {}

    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path,csv_file)
    with open(path, 'r') as csvfile:

        reader = csv.reader(csvfile, delimiter=',', quotechar=',')
        for row in reader:
            if first_row:
                first_row = False
                index = 0
                for name in row:
                    first_row_dict[name] = index
                    index += 1
                    if name == "PGA":
                        break
            else:
                event_id_name = row[0]
                if event_id_name not in data_dict.keys():
                    data_dict[event_id_name] = []
                for key_name in first_row_dict:
                    index = first_row_dict[key_name]
                    if index == 0:
                        aux_dict = {}
                    else:
                        if key_name != 'Station' and key_name != 'Instrument' and key_name != 'T* Class' and key_name != 'P* Class':
                            aux_dict[key_name] = float(row[index])
                        elif key_name == 'PGA':
                            aux_dict[key_name] = parse_scientific_notation(row[index])
                        else:
                            aux_dict[key_name] = row[index]
                data_dict[event_id_name].append(aux_dict)

    return data_dict


def _two_point_line_eq(x, point_1, point_2):
    x1 = point_1[0]
    y1 = point_1[1]
    x2 = point_2[0]
    y2 = point_2[1]
    return (y2 - y1) * ((x - x1)/(x2 - x1)) + y1

def saturated_two_point_line_eq(max_val, point_1, point_2):
    x1 = point_1[0]
    y1 = point_1[1]
    x2 = point_2[0]
    y2 = point_2[1]
    linear_saturated_function = lambda x: (y2 - y1) * ((x - x1)/(x2 - x1)) + y1 if x <= max_val else 1.0
    return linear_saturated_function

def log_function(pga_value):
    #print_as_progress_string("Using log")
    return 0.22 * numpy.log(16.7 * pga_value)

def sigmoid(pga_value):
    #print_as_progress_string("Sigmoid")
    return 1 / (1 + numpy.e ** (-2.1 * (pga_value - 3.03)))

def linear_alpha(pga_value):
    #print_as_progress_string("Using linear_alpha")
    alpha = 0.7
    return ((pga_value - 0.06)/(6.0 - 0.06)) ** alpha

def print_as_progress_string(message):
    """
    Shows message and then deletes it.

    It is meant to simulate something like a progress bar.

    :param message: str
    """
    print("\b" * len(message), end="")
    print(message, flush=True, end="")