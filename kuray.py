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
        self.amplitude = []
        self.phase = []
        self.frequencies = []
        self.length = 3
        self.signal = signals.Signal(30, 20e3, self.length)
        self.create_menu()
        self.create_main_frame()

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
        for _ in range(self.signal.get_length() // CHUNK):
            data = stream.read(CHUNK)
            answer = np.append(answer, np.fromstring(data, 'Int16'))

        fft_input = np.fft.fft(sweep)
        fft_output = np.fft.fft(answer)
        transfer_function = fft_output / fft_input
        self.amplitude = np.abs(transfer_function)
        self.phase = np.angle(transfer_function)

        f_min = self.signal.f_min
        f_max = self.signal.f_max
        number_of_points = 4048
        frequency_ratio = math.log(f_max / f_min) / number_of_points
        self.frequencies = [math.exp(i*frequency_ratio) * f_min
                       for i in range(number_of_points)]
        amplitude_smooth = np.log10(smoothing.smooth(self.amplitude))
        phase_smooth = smoothing.smooth(self.phase)

        self.amplitude_line, = self.axes1.semilogx(self.frequencies,
                                                   amplitude_smooth)
        self.phase_line, = self.axes2.semilogx(self.frequencies, phase_smooth)

        tick_frequencies = [31, 62, 125, 250, 500, 1000,
                            2000, 4000, 8000, 16000]
        ticklabel_frequencies = ['31', '62', '125', '250', '500', '1k',
                                 '2k', '4k', '8k', '16k']
        self.axes1.set_xticks(tick_frequencies)
        self.axes2.set_xticks(tick_frequencies)
        self.axes1.set_xticklabels(ticklabel_frequencies)
        self.axes2.set_xticklabels(ticklabel_frequencies)
        self.canvas.draw()

    def create_menu(self):
        """ Create main menu """
        menu_file = self.menuBar().addMenu('&File')
        menu_help = self.menuBar().addMenu('&Help')

        # Exit button
        act_exit = QtGui.QAction(self)
        act_exit.setText('Exit')
        act_exit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        menu_file.addAction(act_exit)
        act_exit.triggered.connect(self.close)

        # About window
        act_about = QtGui.QAction(self)
        act_about.setText('About')
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
            "QMessageBox.information()", about)
        if reply == QtGui.QMessageBox.Ok:
            self.informationLabel.setText("OK")
        else:
            self.informationLabel.setText("Escape")

    def change_smoothing(self, octave_str):
        """ Change smoothing of graphs. Triggered by `smoothing_combo`. """
        octave = int(octave_str)

        amplitude_smooth = np.log10(smoothing.smooth(self.amplitude, octave))
        phase_smooth = smoothing.smooth(self.phase, octave)
        self.amplitude_line.set_xdata(self.frequencies)
        self.amplitude_line.set_ydata(amplitude_smooth)
        self.phase_line.set_xdata(self.frequencies)
        self.phase_line.set_ydata(phase_smooth)
        self.canvas.draw()

    def change_signal_length(self, length):
        """ Change length of excitation signal """
        self.length = length

    def change_signal_f_min(self, f_min):
        """ Change minimum frequency of excitation signal """
        self.signal.f_min = f_min

    def change_signal_f_max(self, f_max):
        """ Change maximum frequency of excitation signal """
        self.signal.f_max = f_max

    def create_main_frame(self):
        """ Create main frame within the main window. """
        main_frame = QtGui.QWidget()

        signal_param_group = QtGui.QGroupBox("Excitation parameters")
        signal_length_box = QtGui.QDoubleSpinBox(self)
        signal_length_box.setSuffix(" s")
        signal_length_box.setSingleStep(0.1)
        signal_length_box.setValue(self.length)
        signal_length_box.valueChanged.connect(self.change_signal_length)
        signal_length_label = QtGui.QLabel(self)
        signal_length_label.setText("Length in seconds")
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
        smooth_combo = QtGui.QComboBox(self)
        smooth_combo.addItems(["3", "6", "10", "20"])
        # set 1/6 as default value
        smooth_combo.setCurrentIndex(1)
        smooth_combo.activated[str].connect(self.change_smoothing)
        smooth_label = QtGui.QLabel(self)
        smooth_label.setText("Amount of smoothing to be done, in 1/nth octave")
        smooth_hbox = QtGui.QFormLayout()
        smooth_hbox.addRow(smooth_label, smooth_combo)
        smooth_group.setLayout(smooth_hbox)

        fig = mpl.figure.Figure((5.0, 4.0))
        bg_color = main_frame.palette().color(QtGui.QPalette.Window).getRgbF()
        fig.set_facecolor(bg_color)
        self.canvas = FigureCanvas(fig)
        self.canvas.setParent(main_frame)

        measure_button = QtGui.QPushButton("&Measure")
        self.connect(measure_button, QtCore.SIGNAL('clicked()'),
                     self.on_measure)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(signal_param_group)
        vbox.addWidget(smooth_group)
        vbox.addWidget(self.canvas, stretch=1)
        vbox.addWidget(measure_button)

        main_frame.setLayout(vbox)
        self.setCentralWidget(main_frame)

        self.axes1 = fig.add_subplot(2, 1, 1)
        self.axes2 = fig.add_subplot(2, 1, 2)
        self.axes1.semilogx([], [])
        self.axes2.semilogx([], [])
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


def main():
    """ Main function; acts as entry point for Kuray. """
    app = QtGui.QApplication(sys.argv)
    gui = Gui()
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()
