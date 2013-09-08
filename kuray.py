#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Main file of Kuray. Execute it to use the application. """
import numpy as np
import matplotlib as mpl
mpl.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import pyaudio
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import sys
import smoothing

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class Gui(QtGui.QMainWindow):
    """ Gui class for the main window. """

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Kuray")
        self._create_main_frame()

    def _on_measure(self):
        """ Start measurement. """
        # Initialize PortAudio
        port_audio = pyaudio.PyAudio()

        stream = port_audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                                 input=True, output=True, 
                                 frames_per_buffer = CHUNK)

        length = 2**17
        sweep = generate_sweep(length)

        stream.write(sweep)
        answer = []
        for _ in range(length//CHUNK):
            data = stream.read(CHUNK)
            answer = np.append(answer, np.fromstring(data, 'Int16'))

        fft_input = np.fft.fft(sweep)
        fft_output = np.fft.fft(answer)
        transfer_function = fft_output / fft_input

        amplitude_smooth = np.log10(smoothing.smooth(np.abs(transfer_function)))
        phase_smooth = smoothing.smooth(np.angle(transfer_function))

        self.axes1.plot(np.linspace(30, 2e4, len(amplitude_smooth)),
                            amplitude_smooth)
        self.axes2.plot(np.linspace(30, 2e4, len(phase_smooth)),
                            phase_smooth)

        tick_frequencies = [31, 62, 125, 250, 500, 1000,
                            2000, 4000, 8000, 16000]
        ticklabel_frequencies = ['31', '62', '125', '250', '500', '1k',
                                 '2k', '4k', '8k', '16k']
        self.axes1.set_xticks(tick_frequencies)
        self.axes2.set_xticks(tick_frequencies)
        self.axes1.set_xticklabels(ticklabel_frequencies)
        self.axes2.set_xticklabels(ticklabel_frequencies)
        self.canvas.draw()

    def _create_main_frame(self):
        """ Create main frame within the main window. """
        self.main_frame = QtGui.QWidget()
        self.fig = mpl.figure.Figure((5.0, 4.0))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        self.measure_button = QtGui.QPushButton("&Measure")
        self.connect(self.measure_button, QtCore.SIGNAL('clicked()'),
                     self._on_measure)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.measure_button)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

        self.axes1 = self.fig.add_subplot(2, 1, 1)
        self.axes2 = self.fig.add_subplot(2, 1, 2)
        self.line1, = self.axes1.plot([], [])
        self.line2, = self.axes2.plot([], [])
        self.axes1.grid(True)
        self.axes2.grid(True)
        self.axes1.set_xlim(30, 2e4)
        self.axes2.set_xlim(30, 2e4)
        tick_frequencies = [31, 62, 125, 250, 500, 1000, 
                            2000, 4000, 8000, 16000]
        ticklabel_frequencies = ['31', '62', '125', '250', '500', '1k',
                                 '2k', '4k', '8k', '16k']
        self.axes1.set_xticks(tick_frequencies)
        self.axes2.set_xticks(tick_frequencies)
        self.axes1.set_xticklabels(ticklabel_frequencies)
        self.axes2.set_xticklabels(ticklabel_frequencies)

        self.canvas.draw()

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
    app = QtGui.QApplication(sys.argv)
    gui = Gui()
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
