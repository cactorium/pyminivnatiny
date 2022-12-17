import skrf
import numpy as np

class OnePortCalibration:
  def calibrate_s11(self, freqs, iq):
    raise NotImplementedError("use a subclass of this interface")

class SOLCalibration(OnePortCalibration):
  def __init__(self, freqs, iq_open, iq_short, iq_load):
    self.mag = np.sqrt(np.absolute(iq_open)*np.absolute(iq_short))
    self.freqs = skrf.Frequency.from_f(freqs, unit='Hz')
    s_open = skrf.Network(frequency=self.freqs, s=iq_open/mag)
    s_short = skrf.Network(frequency=self.freqs, s=iq_short/mag)
    s_load = skrf.Network(frequency=self.freqs, s=iq_load/mag)
    ideal_open = skrf.Network(frequency=self.freqs, s=np.fill(ip_open.shape[0], 1))
    ideal_short = skrf.Network(frequency=self.freqs, s=np.fill(ip_short.shape[0], -1))
    ideal_load = skrf.Network(frequency=self.freqs, s=np.fill(ip_short.shape[0], 0.0))

    measured = [s_open, s_short, s_load]
    ideals = [ideal_open, ideal_short, ideal_load]
    self.cal = skrf.OnePort(ideal=ideals, measured=measured)
    self.cal.run_cal()

  def calibrate_sl11(self, freqs, iq):
    net = skrf.Network(frequency=freqs, s=iq/self.mag)
    return self.cal.apply_cal(net)

