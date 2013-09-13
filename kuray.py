#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Main file of Kuray. Execute it to use the application. """
import math
import matplotlib as mpl
mpl.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import pyaudio
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import smoothing
import signals
import sys

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class Gui(QtGui.QMainWindow):
    """ Gui class for the main window. """

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Kuray")

        self.freq_response_frame = FrequencyResponseFrame()

        self.create_menu()
        self.setCentralWidget(self.freq_response_frame)

    def create_menu(self):
        """ Create main menu """
        menu_file = self.menuBar().addMenu("&File")
        menu_help = self.menuBar().addMenu("&Help")

        # Exit button
        act_exit = QtGui.QAction(self)
        act_exit.setText("Exit")
        act_exit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        menu_file.addAction(act_exit)
        act_exit.triggered.connect(self.close)

        # About window
        act_about = QtGui.QAction(self)
        act_about.setText("About")
        act_about.setIcon(QtGui.QIcon.fromTheme('help-about'))
        menu_help.addAction(act_about)
        act_about.triggered.connect(self.create_about_window)

    def create_about_window(self):
        """ Creates the about window for Kuray. """

        about = ("Kuray is a cross-platform application for measuring audio"
                "systems. With it, you can obtain amplitude and phase"
                "responses from a loudspeaker. It is still in a very early"
                "stage of development. You can follow its progress on github:"
                "\n \t https://github.com/Psirus/kuray \n"
                "Please report any issues and feature ideas you may have.")

        reply = QtGui.QMessageBox.information(self,
            "About Kuray", about)
        if reply == QtGui.QMessageBox.Ok:
            self.informationLabel.setText("OK")
        else:
            self.informationLabel.setText("Escape")

class FrequencyResponseFrame(QtGui.QWidget):
    """ Measure frequency responses """
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.amplitude = []
        self.phase = []
        self.amplitude_repr = []
        self.phase_repr = []
        self.frequencies = []
        self.smoothing_octave = 6
        self.window_type = 'hamming'
        self.signal = signals.Sweep(30, 20e3, 3)

        signal_param_group = QtGui.QGroupBox("Excitation parameters")
        signal_length_box = QtGui.QDoubleSpinBox(self)
        signal_length_box.setSuffix(" s")
        signal_length_box.setSingleStep(0.1)
        signal_length_box.setValue(self.signal.length)
        signal_length_box.valueChanged.connect(self.change_signal_length)
        signal_length_label = QtGui.QLabel(self)
        signal_length_label.setText("Signal length")
        signal_f_min_box = QtGui.QDoubleSpinBox(self)
        signal_f_min_box.setSuffix(" Hz")
        signal_f_min_box.setValue(self.signal.f_min)
        signal_f_min_box.setRange(20.0, 20e3)
        signal_f_min_box.valueChanged.connect(self.change_signal_f_min)
        signal_f_min_label = QtGui.QLabel(self)
        signal_f_min_label.setText("Lowest frequency")
        signal_f_max_box = QtGui.QDoubleSpinBox(self)
        signal_f_max_box.setSuffix(" Hz")
        signal_f_max_box.setRange(20.0, 20e3)
        signal_f_max_box.setValue(self.signal.f_max)
        signal_f_max_box.valueChanged.connect(self.change_signal_f_max)
        signal_f_max_label = QtGui.QLabel(self)
        signal_f_max_label.setText("Highest frequency")
        signal_param_hbox = QtGui.QFormLayout()
        signal_param_hbox.addRow(signal_length_label, signal_length_box)
        signal_param_hbox.addRow(signal_f_min_label, signal_f_min_box)
        signal_param_hbox.addRow(signal_f_max_label, signal_f_max_box)
        signal_param_group.setLayout(signal_param_hbox)

        smooth_group = QtGui.QGroupBox("Representation")
        octave_combo = QtGui.QComboBox(self)
        octave_combo.addItems(["3", "6", "10", "20"])
        # set 1/6 as default value
        octave_combo.setCurrentIndex(1)
        octave_combo.activated[str].connect(self.change_smoothing)
        octave_label = QtGui.QLabel(self)
        octave_label.setText("Amount of smoothing to be done, in 1/nth octave")

        window_combo = QtGui.QComboBox(self)
        window_combo.addItems(["Hamming Window", "Bartlett Window", 
                               "Blackman Window", "Hanning Window"])
        window_combo.activated[str].connect(self.change_window_type)
        window_label = QtGui.QLabel(self)
        window_label.setText("Window Type:")
        smooth_hbox = QtGui.QFormLayout()
        smooth_hbox.addRow(octave_label, octave_combo)
        smooth_hbox.addRow(window_label, window_combo)
        smooth_group.setLayout(smooth_hbox)

        fig = mpl.figure.Figure((5.0, 4.0))
        bg_color = self.palette().color(QtGui.QPalette.Window).getRgbF()
        fig.set_facecolor(bg_color)
        self.canvas = FigureCanvas(fig)

        measure_button = QtGui.QPushButton("&Measure")
        self.connect(measure_button, QtCore.SIGNAL('clicked()'),
                     self.on_measure)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(signal_param_group)
        vbox.addWidget(smooth_group)
        vbox.addWidget(self.canvas, stretch=1)
        vbox.addWidget(measure_button)
        self.setLayout(vbox)

        self.amplitude_axes = fig.add_subplot(2, 1, 1)
        self.phase_axes = fig.add_subplot(2, 1, 2)
        self.amplitude_axes.semilogx([], [])
        self.phase_axes.semilogx([], [])
        self.amplitude_axes.grid(True)
        self.phase_axes.grid(True)
        self.amplitude_axes.set_xlim(30, 2e4)
        self.amplitude_axes.set_ylim(-18, 18)
        self.phase_axes.set_xlim(30, 2e4)
        self.phase_axes.set_ylim(-180, 180)

        self.set_plot_options()
        self.canvas.draw()

    def update_data_representation(self):
        """ Update lines when changing representation options """
        self.amplitude_repr = 20*np.log10(
                              smoothing.smooth(self.amplitude,
                              self.smoothing_octave, self.window_type))
        self.amplitude_repr = self.amplitude_repr - np.mean(self.amplitude_repr)
        self.phase_repr = smoothing.smooth(self.phase, self.smoothing_octave, 
                                           self.window_type)

    def change_window_type(self, window):
        """ Change window type of smoothing operation """
        # First word in lower case
        self.window_type = window.split()[0].lower()

        self.update_data_representation()
        self.amplitude_line.set_xdata(self.frequencies)
        self.amplitude_line.set_ydata(self.amplitude_repr)
        self.phase_line.set_xdata(self.frequencies)
        self.phase_line.set_ydata(self.phase_repr)
        self.canvas.draw()
        
    def change_smoothing(self, octave_str):
        """ Change smoothing of graphs. Triggered by `smoothing_combo`. """
        self.smoothing_octave = int(octave_str)

        self.update_data_representation()
        self.amplitude_line.set_xdata(self.frequencies)
        self.amplitude_line.set_ydata(self.amplitude_repr)
        self.phase_line.set_xdata(self.frequencies)
        self.phase_line.set_ydata(self.phase_repr)
        self.canvas.draw()

    def change_signal_length(self, length):
        """ Change length of excitation signal """
        self.signal.length = length

    def change_signal_f_min(self, f_min):
        """ Change minimum frequency of excitation signal """
        self.signal.f_min = f_min

    def change_signal_f_max(self, f_max):
        """ Change maximum frequency of excitation signal """
        self.signal.f_max = f_max

    def on_measure(self):
        """ Start measurement. """
        # Initialize PortAudio
        port_audio = pyaudio.PyAudio()

        stream = port_audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                                 input=True, output=True, 
                                 frames_per_buffer = CHUNK)

        sweep = self.signal.generate_sweep()

        stream.write(sweep)
        answer = []
        for _ in range(self.signal.length_in_samples // CHUNK):
            data = stream.read(CHUNK)
            answer = np.append(answer, np.fromstring(data, 'Int16'))

        fft_input = np.fft.fft(sweep)
        fft_output = np.fft.fft(answer)
        transfer_function = fft_output / fft_input
        self.amplitude = np.abs(transfer_function)
        self.phase = np.angle(transfer_function, deg=True)

        f_min = self.signal.f_min
        f_max = self.signal.f_max
        number_of_points = 4048
        frequency_ratio = math.log(f_max / f_min) / number_of_points
        self.frequencies = [math.exp(i*frequency_ratio) * f_min
                       for i in range(number_of_points)]
        self.update_data_representation()

        self.amplitude_line, = self.amplitude_axes.semilogx(self.frequencies,
                                                   self.amplitude_repr)
        self.phase_line, = self.phase_axes.semilogx(self.frequencies,
                                               self.phase_repr)

        self.set_plot_options()
        self.canvas.draw()

    def set_plot_options(self):
        """ Set ticks, ticklabels, labels & titles of plots """
        # x-ticks
        tick_frequencies = [31, 62, 125, 250, 500, 1000,
                            2000, 4000, 8000, 16000]
        ticklabel_frequencies = ["31", "62", "125", "250", "500", "1k",
                                 "2k", "4k", "8k", "16k"]
        self.amplitude_axes.set_xticks(tick_frequencies)
        self.phase_axes.set_xticks(tick_frequencies)
        self.amplitude_axes.set_xticklabels(ticklabel_frequencies)
        self.phase_axes.set_xticklabels(ticklabel_frequencies)

        # y-ticks
        multiples_of_six = mpl.ticker.MultipleLocator(6)
        multiples_of_thirty = mpl.ticker.MultipleLocator(30)

        self.amplitude_axes.yaxis.set_major_locator(multiples_of_six)
        self.amplitude_axes.set_ylim(auto=True)
        self.phase_axes.yaxis.set_major_locator(multiples_of_thirty)
        self.phase_axes.set_ylim(auto=True)

        # Titles
        self.amplitude_axes.set_title("Frequency Response")
        
        # xlabel and ylabel
        self.phase_axes.set_xlabel("Frequency [Hz]")
        self.amplitude_axes.set_ylabel("Amplitude [dB]")
        self.phase_axes.set_ylabel(u"Phase in °")

def main():
    """ Main function; acts as entry point for Kuray. """
    app = QtGui.QApplication(sys.argv)
    gui = Gui()
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
