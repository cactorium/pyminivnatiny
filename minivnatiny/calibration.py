import skrf
import numpy as np

class OnePortCalibration:
  def calibrate_s11(self, freqs, iq):
    raise NotImplementedError("use a subclass of this interface")

class SOLCalibration(OnePortCalibration):
  def __init__(self, freqs, iq_short, iq_open, iq_load):
    self.mag = np.sqrt(np.absolute(iq_open)*np.absolute(iq_short))
    self.fs = freqs
    self.freqs = skrf.Frequency.from_f(freqs, unit='Hz')
    s_open = skrf.Network(frequency=self.freqs, s=iq_open/self.mag)
    s_short = skrf.Network(frequency=self.freqs, s=iq_short/self.mag)
    s_load = skrf.Network(frequency=self.freqs, s=iq_load/self.mag)
    ideal_open = skrf.Network(frequency=self.freqs, s=np.full(iq_open.shape[0], 1))
    ideal_short = skrf.Network(frequency=self.freqs, s=np.full(iq_short.shape[0], -1))
    ideal_load = skrf.Network(frequency=self.freqs, s=np.full(iq_load.shape[0], 0.0))

    measured = [s_open, s_short, s_load]
    ideals = [ideal_open, ideal_short, ideal_load]
    self.cal = skrf.OnePort(ideals=ideals, measured=measured)
    self.cal.run()

  def calibrate_s11(self, fs, iq):
    freqs = skrf.Frequency.from_f(fs, unit='Hz')
    mag = np.interp(fs, self.fs, self.mag)
    net = skrf.Network(frequency=freqs, s=iq/mag)
    return self.cal.apply_cal(net)

