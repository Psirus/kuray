#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Main file of Kuray. Execute it to use the application. """
import numpy as np
import matplotlib.pyplot as plt
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def generate_sweep(length):
    """ Generate sweep with `length` number of samples. """
    amp = 2**15 - 1
    f_start = 30.0 
    f_stop = 20000
    phi = 0.0
    d_phi = 2*np.pi*f_start/RATE

    sweep = np.zeros(length)
    for i in range(length):
        sweep[i] = amp*np.sin(phi)
        phi += d_phi
        d_phi *= 2**(np.log2(f_stop - f_start) / length)

    sweep = np.int16(sweep)
    return sweep

def main():
    """ Main function; acts as entry point for Kuray. """
    # Initialize PortAudio
    port_audio = pyaudio.PyAudio()

    stream = port_audio.open(format = FORMAT, channels = CHANNELS, rate = RATE, 
                             input = True, output = True, 
                             frames_per_buffer = CHUNK)

    length = 2**18
    sweep = generate_sweep(length)

    stream.write(sweep)
    answer = []
    for _ in range(length//CHUNK):
        data = stream.read(CHUNK)
        answer = np.append(answer, np.fromstring(data, 'Int16'))

    fft_input = np.fft.fft(sweep)
    fft_output = np.fft.fft(answer)
    transfer_function = fft_output / fft_input

    plt.subplot(2, 1, 1)
    plt.plot(np.abs(transfer_function))
    plt.subplot(2, 1, 2)
    plt.plot(np.angle(transfer_function, deg=True))
    plt.show()

if __name__ == "__main__":
    main()
