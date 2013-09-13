""" Create excitation signals and store related data """
import numpy as np

RATE = 44100
CHUNK = 1024

class Sweep(object):
    """ Model for excitation signal """

    def __init__(self, f_min=30.0, f_max=20e3, length=3):
        self._f_min = f_min
        self._f_max = f_max
        self.length = CHUNK * int(round(length * RATE // CHUNK))
        
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

    def get_length(self):
        """ Return length of signal in samples """
        return self.length

    def generate_sweep(self):
        """ Generate sweep with `length` number of samples. """
        amp = 2**15 - 1
        phi = 0.0
        d_phi = 2*np.pi*self.f_min/RATE

        sweep = np.zeros(self.length)
        for i in range(self.length):
            sweep[i] = amp*np.sin(phi)
            phi += d_phi
            d_phi *= 2**(np.log2(self.f_max - self.f_min) / self.length)

        sweep = np.int16(sweep)
        return sweep
