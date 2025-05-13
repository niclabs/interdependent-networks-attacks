""" This script contains all the functions associated to seismic data
processing.

TODO: documentation
"""

import csv
import numpy
import os


def get_chile_pga(Mw, H, Feve, R, St_t, Vs30):
    c1 = -2.8548
    c2 = 0.7741
    c3 = -0.97558
    c4 = 0.1
    c5 = -0.00174
    c6 = 5
    c7 = 0.35
    c8 = 0.00586
    c9 = -0.03958
    delta_c1 = 2.5699
    delta_c2 = -0.4761
    delta_c3 = -0.52745
    h0 = 50  # 50 km
    Mr = 5
    Vref = 1530  # 1530 m/s

    if Feve == 0:
        delta_fm = c9 * (Mw ** 2)
    else:
        delta_fm = delta_c1 + delta_c2 * Mw

    Ff = c1 + c2*Mw + c8*(H - h0)*Feve + delta_fm

    g = (c3 + c4*(Mw - Mr) + delta_c3*Feve)
    R0 = ((1 - Feve)*c6 * 10**(c7*(Mw - Mr)))

    Fd = g*numpy.log10(R + R0) + c5*R

    Fs = St_t*numpy.log10(Vs30/Vref)

    log10_pga = Ff + Fd + Fs

    pga = 10 ** log10_pga
    return pga

def soil_value(vs30):
    soil_coef = -0.506
    #print("Using Soil coef: {}".format(soil_coef))
    return soil_coef#-0.322


def km_to_coordinates_chile(kms):
    coordinate = 20
    km = 175
    factor = coordinate / km  # "coordinate" per km
    return kms * factor

def coordinates_to_km_chile(coordinates):
    coordinate = 20
    kms = 175
    factor = kms/coordinate # kms per unit of "coordinate"
    return coordinates*factor

def get_chile_pga2(Mw, H, Feve, R, St_t, Vs30):
    #print("Using eq for T = 0.3s")
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
    #print("Using soil coef: {}".format(St_t))
    if Feve == 0:
        delta_fm = c9 * (Mw ** 2)
    else:
        delta_fm = delta_c1 + delta_c2 * Mw

    Ff = c1 + c2*Mw + c8*(H - h0)*Feve + delta_fm

    g = (c3 + c4*(Mw - Mr) + delta_c3*Feve)
    R0 = ((1 - Feve)*c6 * 10**(c7*(Mw - Mr)))

    Fd = g*numpy.log10(R + R0) + c5*R

    Fs = St_t*numpy.log10((Vs30+0.00000000000001)/Vref)

    log10_pga = Ff + Fd + Fs

    pga = 10 ** log10_pga
    return pga

def linear_shindo_scale_probability(pga):
    #print("Using linear probabilities")
    gravity_acceleration = 9.81
    ms_pga = pga * gravity_acceleration
    # print("-------------")
    # print("pga: {}, ms_pga: {}".format(pga, ms_pga))
    if ms_pga > 4:
        return 1
    else:
        prob_value = two_point_line_eq(ms_pga, (0.06, 0.0), (6.0, 1.0))
        if prob_value < 0:
            prob_value = 0
        # print("---> failure prob: {}".format(prob_value))
        # print("-------------")
        return prob_value

def shindo_scale_probability(pga):
    gravity_acceleration = 9.8
    ms_pga = pga * gravity_acceleration
    tiers = {#"0": (0, 0.008),
             #"1": (0.008, 0.025),
             #"2": (0.025, 0.08),
             #"3": (0.08,0.25),
             "4": [(0.25, 0.80), (0.01, 0.1)], # delta = 0.55 -> 0.8 m/s => 10% damage probability
             "5-": [(0.8, 1.4), (0.1, 0.2)], # delta = 0.6 -> 1.4 m/s => 20% damage probability
             "5+": [(1.4, 2.5), (0.2, 0.5)], # delta = 1.1 -> 2.5 m/s => 50% damage probability
             "6-": [(2.5, 3.15), (0.5, 0.85)], # delta = 0.65 -> 3.15 m/s => 85% damage probability
             "6+": [(3.15, 4), (0.85, 1)], # delta = 0.85 -> 4 m/s => 100% damage probability
             "7": [(4, float('inf')), (1, 1)]}

    for tier_number in tiers:
        if tiers[tier_number][0][0] <= ms_pga < tiers[tier_number][0][1]:
            point_1 = (tiers[tier_number][0][0], tiers[tier_number][1][0])
            point_2 = (tiers[tier_number][0][1], tiers[tier_number][1][1])
            prob_value = two_point_line_eq(ms_pga, point_1, point_2)
            return prob_value
    return 0

def load_seismic_data_from_file(seismic_data_file):
    data_dict = load_from_csv(seismic_data_file)
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


def load_from_csv(csv_file):

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


def get_chile_vs30(Mw, H, Feve, R, St_t, pga):
    c1 = -2.8548
    c2 = 0.7741
    c3 = -0.97558
    c4 = 0.1
    c5 = -0.00174
    c6 = 5
    c7 = 0.35
    c8 = 0.00586
    c9 = -0.03958
    delta_c1 = 2.5699
    delta_c2 = -0.4761
    delta_c3 = -0.52745
    h0 = 50  # 50 km
    Mr = 5
    Vref = 1530  # 1530 m/s

    if Feve == 0:
        delta_fm = c9 * (Mw ** 2)
    else:
        delta_fm = delta_c1 + delta_c2 * Mw

    Ff = c1 + c2*Mw + c8*(H - h0)*Feve + delta_fm

    g = (c3 + c4*(Mw - Mr) + delta_c3*Feve)
    R0 = ((1 - Feve)*c6 * 10**(c7*(Mw - Mr)))

    Fd = g*numpy.log10(R + R0) + c5*R

    log10_pga = numpy.log10(pga)

    if St_t != 0:
        Vs30 = (10 ** ((log10_pga - Ff - Fd) / St_t)) * Vref
    else:
        Vs30 = Vref

    return Vs30


def get_vs30_from_data_in_csv(csv_file):
    data = load_from_csv(csv_file)
    vs30_list = []
    for event_id in data:
        for event in data[event_id]:
            Mw = event["Magnitude"]
            H = event["Depth"]
            Feve = event["Fault Type"]
            R = event["Distance"]
            site_type = event["T* Class"]
            St_t = site_reference(site_type)
            pga = event["PGA"]
            vs30 = get_chile_vs30(Mw, H, Feve, R, St_t, pga)
            vs30_list.append({"T* Class": site_type, "Vs30": vs30})
    return vs30_list


def shindo_scale_probability(pga):
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
            prob_value = two_point_line_eq(ms_pga, point_1, point_2)
            return prob_value
    return 0


def two_point_line_eq(x, point_1, point_2):
    x1 = point_1[0]
    y1 = point_1[1]
    x2 = point_2[0]
    y2 = point_2[1]
    return (y2 - y1) * ((x - x1)/(x2 - x1)) + y1

def my_init():
    pgas = []
    soils = ['III']
    for soil in soils:
        St_t = site_reference(soil)
        Mw = 8.8
        Feve = 0
        R = 100.5
        H = 28.1
        Vs30 = 700

        R = 50
        pga = get_chile_pga(Mw, H, Feve, R, St_t, Vs30)
        pgas.append(pga)
        shindo = shindo_scale_probability(pga)
        print("soil {} : pga = {}, shindo prob = {} ".format(soil, pga, shindo))

        R = 100
        pga = get_chile_pga(Mw, H, Feve, R, St_t, Vs30)
        pgas.append(pga)
        shindo = shindo_scale_probability(pga)
        print("soil {} : pga = {}, shindo prob = {} ".format(soil, pga, shindo))

        R = 200
        pga = get_chile_pga(Mw, H, Feve, R, St_t, Vs30)
        pgas.append(pga)
        shindo = shindo_scale_probability(pga)
        print("soil {} : pga = {}, shindo prob = {} ".format(soil, pga, shindo))


    dip = load_from_csv('seismic_data.csv')

    for k in dip.keys():
        print(k)
        print(dip[k])

def test():

    a = load_from_csv('seismic_data.csv')


    ssum = 0

    for k in a.keys():
        ssum += len(a[k])
