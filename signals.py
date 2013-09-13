""" Create excitation signals and store related data """
import numpy as np

RATE = 44100
CHUNK = 1024

class Sweep(object):
    """ Model for excitation signal """

    def __init__(self, f_min=30.0, f_max=20e3, length=3):
        self._f_min = f_min
        self._f_max = f_max
        self._length_in_samples = CHUNK * int(round(length * RATE // CHUNK))
        self._length = self.length_in_samples // RATE
        
    @property
    def f_min(self):
        """ Lowest frequency """
        return self._f_min

    @f_min.setter
    def f_min(self, f_min):
        """ Set minimum frequency """
        self._f_min = f_min

    @property
    def f_max(self):
        """ Highest frequency """
        return self._f_max

    @f_max.setter
    def f_max(self, f_max):
        """ Set maximum frequency """
        self._f_max = f_max

    @property
    def length(self):
        """ Signal length in seconds """
        return self._length

    @length.setter
    def length(self, length):
        """ Set signal length (seconds) """
        self._length_in_samples = CHUNK * int(round(length * RATE // CHUNK))
        self._length = self._length_in_samples // RATE

    @property
    def length_in_samples(self):
        """ Signal length in number of samples """
        return self._length_in_samples

    @length_in_samples.setter
    def length_in_samples(self, length_in_samples):
        """ Set signal length (samples) """
        self._length_in_samples = CHUNK * int(round(length_in_samples // CHUNK))
        self._length = self._length_in_samples // RATE

    def generate_sweep(self):
        """ Generate sweep with `length` number of samples. """
        amp = 2**15 - 1
        phi = 0.0
        d_phi = 2*np.pi*self.f_min/RATE

        sweep = np.zeros(self.length_in_samples)
        for i in range(self.length_in_samples):
            sweep[i] = amp*np.sin(phi)
            phi += d_phi
            d_phi *= 2**(np.log2(self.f_max - self.f_min) 
                    / self.length_in_samples)

        sweep = np.int16(sweep)
        return sweep
