import numpy as np

# TODO add __enter__ and __exit__ methods
class VNA:
  def __init__(self, port=None):
    if port is not None:
      if isinstance(port, str):
        self.port = serial.Serial(port)
      elif isinstance(port, serial.Serial):
        self.port = port
      else:
        raise ValueError("you can only pass a string or Serial object into the VNA")

      self.port.baudrate = 921600
      self.port.parity = serial.PARITY_NONE
      self.port.stopbits = serial.STOPBITS_ONE
      self.port.rtscts = False
      self.port.dsrdtr = False
      if not self.port.is_open:
        self.port.open()
    else:
      raise NotImplementedError("currently none port type is not implemented")

  def close(self):
    self.port.close()

  def send_cmd(self, msg):
    self.port.flushInput()
    self.port.write(msg)
    return self.port.read_until()

  def firmware_info(self):
    return self.send_cmd(b"9\x0d")

  def device_supply(self):
    self.port.flushInput()
    self.port.write(b"8\x0d")
    dat = self.port.read(2)
    if len(dat) < 2:
      return ValueError("did not receive valid device supply voltage")
    return ((dat[1] << 8) | dat[0]) * 6 / 1024.0

  def device_temperature(self):
    self.port.flushInput()
    self.port.write(b"10\x0d")
    dat = self.port.read(2)
    if len(dat) < 2:
      return ValueError("did not receive valid device supply voltage")
    return ((dat[1] << 8) | dat[0]) / 10.0

  def read_raw(self, start_freq, end_freq, num_samples):
    freqs = np.linspace(start_freq, end_freq, num_samples)
    iq = np.zeros(num_samples, dtype=np.complex128)
    # 3 bytes per ADC reading (I guess)
    # 4 readings per sample, I guess it's a differential
    # pair thing
    # TODO experiment with reading it all at once vs reading one sample at a time
    dat = self.port.read(12*num_samples)
    if len(dat) < 12*num_samples:
      raise RuntimeError("did not receive sufficient data from scan, {} < {}".format(len(dat), 12*num_samples))
    for i in range(num_samples):
      p1 = dat[12*i] + (dat[12*i+1] << 8) + (dat[12*i+2] << 16)
      p2 = dat[12*i+3] + (dat[12*i+4] << 8) + (dat[12*i+5] << 16)
      p3 = dat[12*i+6] + (dat[12*i+7] << 8) + (dat[12*i+8] << 16)
      p4 = dat[12*i+9] + (dat[12*i+10] << 8) + (dat[12*i+11] << 16)
      iq[i] = (p1 - p3)/2. + 1j*(p2 - p4)/2.
    return freqs, iq


  def send_freq(self, freq):
    if freq < 1e+6 or freq > 3e+9:
      raise ValueError("frequency is out of VNA's range")
    internal_freq = freq // 10
    self.port.write(bytes(str(internal_freq), "utf8"))
    self.port.write(b"\x0d")

  def start_frequency_generator(self, freq):
    self.port.flushInput()
    self.port.write(b"21\x0d")
    self.send_freq(freq)
    self.send_freq(freq)
    self.port.write(b"1\x0d")
    self.port.write(b"0\x0d")
    _ = self.read_raw(0, 1, 1)

  def stop_frequency_generator(self):
    self.port.flushInput()
    self.port.write(b"7\x0d")
    self.port.write(b"0\x0d")
    self.port.write(b"0\x0d")
    self.port.write(b"1\x0d")
    self.port.write(b"0\x0d")
    dat = self.read_raw(0, 1, 1)

  def raw_iq_refl(self, start_freq, end_freq, num_samples):
    if end_freq < start_freq:
      raise ValueError("invalid frequency range selected")
    self.port.flushInput()
    self.port.write(b"7\x0d")
    self.send_freq(start_freq)
    self.send_freq(end_freq)
    self.port.write(bytes(str(num_samples), "utf8") + b"\x0d")
    self.port.write(b"\x0d")
    dat = self.read_raw(start_freq, end_freq, num_samples)

    self.stop_frequency_generator()
    return dat

  def raw_iq_refl_ranges(vna, freq_ranges):
    freqs = []
    iqs = []
    for start, end, num_samples in freq_ranges:
      f, iq = vna.raw_iq_trans(start, end, num_samples)
      freqs.append(f)
      iqs.append(iq)
    return np.concatenate(freqs), np.concatenate(iqs)


  def raw_iq_trans(self, start_freq, end_freq, num_samples):
    self.port.flushInput()
    self.port.write(b"6\x0d")
    self.send_freq(start_freq)
    self.send_freq(end_freq)
    self.port.write(bytes(str(num_samples), "utf8") + b"\x0d")
    self.port.write(b"\x0d")
    dat = self.read_raw(start_freq, end_freq, num_samples)

    self.stop_frequency_generator()
    return dat

class CalibratedVNA(VNA):
  def __init__(self, tiny, calibration):
    self.port = tiny.port
    self.cal = calibration

  def scan_s11(self, min_freq, max_freq, num_steps):
    freqs, iq = self.raw_iq_refl(min_freq, max_freq, num_steps)
    return self.cal.calibrate_s11(freqs, iq)

  def scan_s11_ranges(self, freq_ranges):
    # TODO
    pass

  def scan_s21(self, min_freq, max_freq, num_steps):
    freqs, iq = self.raw_iq_trans(min_freq, max_freq, num_steps)
    raise NotImplementedError("yeah this needs work")
