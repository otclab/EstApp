#!python
# -*- coding: UTF-8 -*-

import vxi11

class VACMeasure(object) :
  def __init__(self, dmm):
    """
      Selecciona la función de medición de tensión alterna y fija la escala a utilizarce en
      las subsiguientes mediciones, por medio de la función de selección de escala automática
      del instrumento. Y prepara el instrumento para el calculo de las estadísticas de la
      medición.

      Requisitos : La tensión a medir debe estar presente en este momento.
      """
    self.dmm = dmm.dmm

    # Fija la función y reliza el ajuste de escala automáticamente :
    self.dmm.write("CONF:VOLT:AC AUTO")
    self.dmm.write("SENS:VOLT:AC:RANG:AUTO ONCE")
    self.dmm.ask("SAMP:COUN 2")
    self.dmm.ask("READ?")

    # Prepara para una medición indefinida :
    self.dmm.write("TRIG:SOURC:IMM")
    self.dmm.write("TRIG:COUN 1")
    self.dmm.write("SAMP:COUN 1000")

    # Prepara par el cálculo de las propiedades estadísticas de la medición :
    self.dmm.write("CALC:AVER:STAT ON")
    self.dmm.write("CALC:AVER:CLE")

    self.__samples = []
    self.__done = False
    self.__avg = None
    self.__max = None
    self.__min = None


  @property
  def count(self):
    return int(float(self.dmm.ask('CALC:AVER:COUN?')))

  @property
  def samples(self):
    if not self.__done :
      self.__samples.append([float(x) for x in self.dmm.ask("READ?").split(',')])
    return self.__samples

  @property
  def avg(self):
    if not self.__done :
      return float(self.dmm.ask('CALC:AVER:AVER?'))

    if self.__avg is None :
      self.__avg = float(self.dmm.ask('CALC:AVER:AVER?'))

    return self.__avg

  @property
  def max(self):
    if not self.__done :
      return float(self.dmm.ask('CALC:AVER:MAX?'))

    if self.__max is None:
      self.__max = float(self.dmm.ask('CALC:AVER:MAX?'))

    return self.__max


  @property
  def min(self):
    if not self.__done :
      return float(self.dmm.ask('CALC:AVER:MIN?'))

    if self.__min is None:
      self.__min = float(self.dmm.ask('CALC:AVER:MIN?'))

    return self.__min


  def start_measure(self):
    self.dmm.write("INIT")


  def stop_measure(self):
    self.dmm.write("ABOR")
    self.__done = True



class SDM3055(object) :
  def __init__(self, ip):
    # Sa conecta al dispositivo con la dirección IP dada :
    try :
      self.dmm = vxi11.Instrument(ip)
    except :
      raise Exception("Not Found.")

    # Verifica que se trata del modelo correcto :
    self.__idn = self.dmm.ask("*IDN?")
    self.__idn = self.__idn.split(',')

    if (len(self.__idn) < 1) or not (self.__idn[1] == "SDM3055") :
      raise Exception("Not supported.")

  @property
  def manufacturer(self) :
    return self.__idn[0]

  @property
  def model(self) :
    return self.__idn[1]

  @property
  def num_serie(self):
    return self.__idn[2]



if __name__ == '__main__':
  """
  Ejemplo del uso de las clases SDM3055 y VACMeasure
  """
  import winsound
  from time import sleep

  def short_beep():
    # Tono de 2500Hz generado durante 120 mS.
    winsound.PlaySound('..\\beeps\\short_beep.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)


  def long_beep():
    # Tono de 2500Hz generado durante 1000 mS.
    winsound.PlaySound('..\\beeps\\long_beep.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)


  def measuring(dmm_measure, start_count_down=5, length_count_down=20):
    # Cuenta regresiva para el inicio de la medición :
    for i in range(0, start_count_down):
      print('Inicio en : %2d\x0D' % (start_count_down - i), end=' ')
      short_beep()
      sleep(1)
    long_beep()
    sleep(1)

    # Se inicia la medición :
    dmm_measure.start_measure()

    # Medición, cuenta regresiva y presentación de su progreso :
    for i in range(0, length_count_down):
      print('Final en %d :  ' % (length_count_down - i), end=' ')
      print('[L-N] %6.2f[%+2.5e / %+2.5e], \x0D' %(dmm_measure.avg, dmm_measure.max - dmm_measure.avg, dmm_measure.min - dmm_measure.avg), end=' ')

      if (i == (length_count_down - 1)):
        long_beep()
      else:
        short_beep()

      sleep(1)

    dmm_measure.stop_measure()

    # Presentación de los resultados :
    print('Resumen de la medición (%d samples):\n    ' % dmm_measure.count, end=' ')
    print(' %6.2f V [%+2.2fV / %+2.2fV], ' % (dmm_measure.avg, dmm_measure.max - dmm_measure.avg, dmm_measure.min - dmm_measure.avg))


  # Conecta con el multímetro :
  DMM = SDM3055("192.168.112.124")
  print('Modelo %s de %s, Nº %s' %(DMM.model, DMM.manufacturer, DMM.num_serie))

  # Prepara la medición :
  dmm_measure = VACMeasure(DMM)

  # Presenta el Resultado de la medición, mientras se encuentra en progreso presenta los resultados parciales :
  measuring(dmm_measure)

