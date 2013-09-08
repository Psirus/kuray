""" Smooth frequency response """

import numpy as np
import math

def _distribute_over_log(input_data, f_min, f_max, number_of_points):
    """ Distribute linear input data over logarithmic frequency scaling """

    frequency_ratio = math.log(f_max / f_min) / number_of_points
    frequencies = [math.exp(i*frequency_ratio) * f_min
                        for i in range(number_of_points)]

    log_data = []
    for freq in frequencies:
        index = round((freq - f_min) / (f_max - f_min) * len(input_data))
        log_data.append(input_data[index])

    return log_data

def smooth(input_data, nth_octave = 6):
    """ Smooth input data over 1/n octave """

    f_min = 30
    f_max = 20e3

    number_of_octaves = math.log(f_max / f_min, 2)

    # ideally, this should be computed from the display resolution
    number_of_points = 4048
    points_per_octave = number_of_points / number_of_octaves

    log_data = _distribute_over_log(input_data, f_min, f_max, number_of_points)

    window_length = points_per_octave / nth_octave

    window = np.hamming(window_length)
    output = np.convolve(window / window.sum(), log_data, mode='same')
    return output
