#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Oscar'

import math
import threading
from otcCard.OTCProtocol import *
from otcCard import *
from report import report
import logging
import Queue

class Measure_Statistics(object) :
   """
   Contenedor para el registro básico de las mediciones, i.e. el cálculo de
   los valores efectivo (rms), máximo (max) y mínimo (min). desde el cuadrado
   de su magnitud 'instantánea'.
   """
   def __init__(self, scale) :
      self._scale = scale
      self.arm()

   def arm(self) :
      self._max = 0
      self._min = 2**24 - 1
      self._avg = 0L
      self._count = 0

   def add(self, sample) :
      self._avg += sample
      if self._max < sample : self._max = sample
      if self._min > sample : self._min = sample

      self._count += 1

   def max(self) :
      return math.sqrt(float(self._max))*self._scale

   def min(self) :
      return math.sqrt(float(self._min))*self._scale

   def rms(self) :
      if self._count == 0 :
         return 0
      return math.sqrt(float(self._avg)/self._count) * self._scale


class ModeFlags(object) :
  """
  Contenedor de las banderas de activación y selección del modo de trabajo.
  (aka. Cfg.CtrlCfg.ModeFun).
  """
  class Flag(object) :
     def __init__(self, pos, name, one_val, cero_val) :
       self.mask = 1 << pos
       self.name = name
       self.cero_val = cero_val
       self.one_val  = one_val

     def __set__(self, obj, val) :
       if val.lower() in [self.cero_val.lower(), u'off', u'0'] :
         obj.card._modeFunctions &= (~self.mask)
       elif val.lower() in [self.one_val.lower(), u'on', u'1'] :
         obj.card._modeFunctions |= self.mask
       else :
         raise ValueError(u'\'%s\' no es un valor admisible para : %s' % (val, self.name))

     def __get__(self, obj, objtype) :
       return self.one_val if obj.card._modeFunctions & self.mask != 0 else self.cero_val

     def __unicode__(self) :
       if self.name[-2:] in [u'ón', u'da'] :
         msg = u'La '
       else :
         msg = u'La función de '

       msg += self.name
       msg += u'esta' if self.one_val[-1] != u'a' else u'es'
       msg = self.__get__(self, None)

       return msg


  inputEnable     = Flag(0, u'Entrada de Coordinación', u'Activa', u'Inactiva')
  outputEnable    = Flag(1, u'Salida de Coordinación', u'Activa', u'Inactiva')
  expansionEnable = Flag(2, u'Expansión', u'Habilitada', u'Deshabilitada')
  inputSelection  = Flag(3, u'Selección de Entrada', u'UV', u'LN')
  feedbackEnable  = Flag(4, u'Realimentación', u'Activa', u'Inactiva')
  splitEnable     = Flag(5, u'Taps Superpuestos', u'Activa', u'Inactiva')

  def __init__(self, card) :
    self.card = card

  @staticmethod
  def functionNames() :
    return [p.name for p in ModeFlags.__dict__.values()
                                       if type(p) == ModeFlags.Flag ]

  @staticmethod
  def getFunctionOf(name):
    n_desc, desc = [(n,d) for n, d in ModeFlags.__dict__.items()
              if (type(d) == ModeFlags.Flag) and (d.name == name)][0]
    return n_desc

  def getStatusStr(self, name):
    # Obtiene el nombre del atributo del y el descriptor con el nombre de
    # función dado (name) :
    n_desc, desc = [(n,d) for n, d in ModeFlags.__dict__.items()
             if (type(d) == ModeFlags.Flag) and (d.name == name)][0]

    str = u'%s : %s' %(name, getattr(self, n_desc))

    return str

  def __unicode__(self) :
    txt = u''
    for name, desc in ModeFlags.__dict__.items() :
      if type(desc) == ModeFlags.Flag :
        txt += u'%25s : %s\n' %(desc.name, getattr(self, name))

    return txt


class Phase(object) :
  """
  Contenedor de los parámetros asociados a las fases de medición (LN y UV) :
  nombre (name), ganancia (gain) y el resultado de las valores estadísticos
  básicos de la medición asociada (min, max, rms) como su representación.
  """
  # TO DO : Levantar una excepción si se accede a la medición antes de
  # ejecutarla :

  def __init__(self, card, name) :
    self.card  = card
    self.name  = name
    self.stats = Measure_Statistics((self.card.scale /
                                     math.sqrt(self.gain/EstCard1V0.GAIN_NOM)))

  @property
  def gain(self) :
    return getattr(self.card, '_gain'+self.name[0])

  @property
  def max(self) :
    return self.stats.max()

  @property
  def min(self) :
    return self.stats.min()

  @property
  def rms(self) :
    return self.stats.rms()

  def add(self, value) :
      self.stats.add(value)

  def __str__(self) :
    if (abs(self.max - self.rms) < 10) and                               \
                                       (abs(self.rms - self.min) < 10) :
      return u'%6.2f (+%4.2f/-%4.2f)' % (self.rms,
                                self.max - self.rms, self.rms - self.min)
    else :
      return u'%6.2f ( -.--/ -.--)' % (self.rms)


class MeasureTask(threading.Thread) :
  """
  Hilo de ejecución para la medición (y registro) de las tensiones L-N y U-V.
  Como es usual es iniciada por el método start() y detenida ajustandoa False
  su variable started, al invocar el método stop().
  """
  def __init__(self, card) :
    # Se prepara el hilo de ejecución, para su arranque :
    threading.Thread.__init__(self)

    self.card = card

    # Se inicializa la estadística de medición de cada fase :
    card.LN.stats.arm()
    card.UV.stats.arm()

    self.started = False

    self.queue = Queue.Queue(1000)

  def run(self) :
    self.card.log.debug(u'Measure Thread has started')
    self.started = True
    self.error = None
    err_cnt = 0

    # Durante la etapa de medición se tolera cierto número de errores,
    # que no son necesario reportarlos en la consola, solo los errores
    # críticos son propagados a esta :
    report.consoleSetLevel(logging.CRITICAL)

    try :
      while (self.started and (err_cnt < 10)) :
        try :
          record_measure = self.card._measure_record

          self.card.LN.add(record_measure[1])
          self.card.UV.add(record_measure[2])
          self.err_cnt = 0

          # Retira el elemento mas antiguo de la cola se esta llena :
          if self.queue.full() : self.queue.get()

          self.queue.put(record_measure)

        except OTCProtocolError as e :
          err_cnt += 1

    except :
       report.consoleSetLevel(logging.ERROR)
       self.error = u'Fallo inesperado durante la Medición.'
       self.card.log.critical(u'Fallo inesperado durante la Medición.')

    finally :
      # Se restaura la propagación de los errores a la consola :
      report.consoleSetLevel(logging.ERROR)

      self.started = False

      self.card.log.debug(u'Measure Thread has stoped')

      if err_cnt >= 10 :
        self.error = u'Fallo la Medición, demasiados errores.'
        self.card.log.critical(u'Fallo la Medición, demasiados errores.')


  def stop(self) :
    self.started = False


# CalibrationFactor contiene la representación del factor de calibración de
# las entradas. Sus atributos (read-only) effective e internal entregan la
# ganancia real y la representación interna (en el microcontrolador).
#
# Se crea especificando además de la entrada a la que pertenece y el valor de
# uno de ellos nominandolos explícitamente.
#
# También incluye el método __unicode__ para representar la ganancia real y
# representación interna simultaneamente.
class CalibrationFactor1V0(object) :
  def __init__(self, input, **kwargs):
    self.input = input

    if (len(kwargs) == 1) and (kwargs.keys()[0] == 'internal') :
      self._bin = kwargs['internal']
      return

    elif (len(kwargs) == 1) and (kwargs.keys()[0] == 'effective') :
      if input == 'V' :
        # El factor de amplificación de la entrada V esta dado por la
        # ecuación :
        #    dec = 1 + (1/16)*((bin/128)/(0xCD29/0x10000)
        #    dec = 1 + (1/16)*((bin/128)/0.8014)
        #    dec = 1 + (bin/128)/12.8225
        #    dec = 1 + bin/1641.28
        # y :
        #    bin = 1641.28*(dec - 1)
        print 'effective = ', kwargs['effective']
        dec2hex = lambda x :int(x) if x >= 0 else 256 + int(x)
        cal = int(1641.28*(kwargs['effective'] - 1))
        print 'cal = ', cal
        self._bin = dec2hex(cal)
        print 'internal = ', self._bin
        if abs(cal) > 127 :
          raise ValueError('Error - El factor de calibracion (%f) excede el '
                           'rango.' %self._bin)

      else :
        self._bin = (kwargs['effective']**2)*EstCard1V0.GAIN_NOM
        if self._bin > 65535 :
          raise ValueError('Error - El factor de calibracion (%f) excede el '
                           'rango.'% self._bin)
      return

    raise ValueError('CalibrationFactor debe invocarse definiendo solo uno de'
                     ' los siguientes argumentos explicitos : effective = ...'
                     ' o internal = ...')

  @property
  def effective(self):
    if self.input == 'V' :
      hex2dec = lambda x : x if x <= 128 else (x-256)
      return 1 + hex2dec(self._bin)/1641.28
    else :
      return math.sqrt(self._bin/EstCard1V0.GAIN_NOM)

  @property
  def internal(self):
    return self._bin

  def __unicode__(self):
    if self.input == 'V' :
      return u'%6.4f [0x%02X]' %(self.effective, self.internal)
    else :
      return u'%6.4f [0x%04X]' %(self.effective, self.internal)


def ThresholdSetFactory(card) :
  u'''
  Devuelve el vector de Umbrales del dispositivo card. El vector de umbrales
  es un objeto del tipo (adhoc) ThresholdList cuyos elementos contienen dos
  atributos sup e inf, que representan los umbrales del tap respectivo.
  '''

  # scaled_param devuelve el objeto del tipo ScaledParameter que contiene al
  # parámetro (del tipo CardParameter) card_parameter., con las funciones de
  # conversión adecuadas para representar los umbrales del dispositivo.
  scaled_param = lambda card_parameter : ScaledParameter( card_parameter,
               [lambda x : card.scale *math.sqrt(x*card.GAIN_NOM/65536),
                lambda x : int((x/card.scale)**2 * 65536/card.GAIN_NOM + 0.5)],
                [0, 32768],
                r'%6.2f [0x%04X]')

  def tap_threshold(i, adr) :
    u'''
    Devuelve un objeto (TapThreshold) con dos atributos : sup e inf, del tipo
    ScaledParameter, del los umbrales superior e inferior del tap, cuya dire-
    cción de almacenamiento en el dispositivo es adr.
    Adicionalmente provee una presentación estandarizada para el par de los
    umbrales del tap y la capacidad de leer y modificar el número de taps
    operativos por medio de su propiedad len.
    '''
    class TapThreshold(object) :
      __sup = CardParameter(adr   , '<H', u'Umbral Superior #%i de Tensión' %i)
      sup = scaled_param(__sup)

      __inf = CardParameter(adr + 2,'<H', u'Umbral Inferior #%i de Tensión' %i)
      inf = scaled_param(__inf)

      def __init__(self, card):
        self.card = card

      def __str__(self):
        return 'sup = %s , inf = %s' %(self.sup, self.inf)

    return TapThreshold(card)

  class ThresholdList(object) :
    # TODO Parametro para reajustar el número de taps utilizados,
    __tapsOpRange = CardParameter(card.tapsOpRangeAdr, '<B', u'Taps Utilizados')

    def __init__(self) :
      self.card = card
      self.thresholds = list()

      for i in range(0, card.tapLimit) :
        self.thresholds.append(tap_threshold(i, card.thresholdsAdr + 4*i))

    def __getitem__(self, item):
      return self.thresholds[item]

    def __len__(self):
      return self.__tapsOpRange

    @property
    def len(self):
      return self.__tapsOpRange

    @len.setter
    def len(self, number_of_taps):
      if number_of_taps > card.tapLimit :
        raise ValueError('El numero de taps solicitados (%d) excede la '
                                                 'capacidad del dispositivo.' )
      self.__tapsOpRange = number_of_taps

    def __str__(self):
      txt = '  Tap     Superior         Inferior\n'
      for i in range(self.len) :
        txt += '   %d   %s  %s\n' %(i + 1, self.thresholds[i].sup,
                                                        self.thresholds[i].inf)
      return txt

  return ThresholdList()


def getAttributeParameter(name, container, typ) :
  for p in container.__dict__.keys() :
    if isinstance(container.__dict__[p], typ) :
      if container.__dict__[p].name == name :
        return p

  return None

def isAttributeName(name, container, typ) :
  return name in [container.__dict__[p].name
                   for p in container.__dict__.keys() if isinstance(container.__dict__[p], typ)]


class EstCard1V0(OTCCard) :
  u'''
  Clase para representar el modelo de la tarjeta EstCard 1V0 :
  '''

  # Direcciones y Tamaño de las áreas de memoria :
  flashAdr               = 0x0000
  flashSize              = 0x1000
  ramAdr                 = 0xE000
  ramSize                = 0x0100
  eepromAdr              = 0xF000
  eepromSize             = 0x0100

  # Direcciones de los parámetros de la tarjeta :
  paswordAdr             = 0xE400
  measureModeAdr         = 0xE000
  measureAdr             = 0xE408
  tapStatusAdr           = 0xE40D

  underVoltageTurnOnAdr  = 0xF000
  overVoltageTurnOnAdr   = 0xF002
  underVoltageTurnOffAdr = 0xF004
  overVoltageTurnOffAdr  = 0xF006

  tapsOpRangeAdr         = 0xF008
  modeFunAdr             = 0xF009

  gainLAdr               = 0xF00A
  gainUAdr               = 0xF00C
  gainVAdr               = 0xF00E

  scaleAdr               = 0xF00F

  thresholdsAdr          = 0xF01F

  clientAdr              = 0xF053
  dateAdr                = 0xF064
  serieAdr               = 0xF06B
  vinAdr                 = 0xF072
  voutAdr                = 0xF079
  regAdr                 = 0xF07F
  rsAdr                  = 0xF084
  rdAdr                  = 0xF089
  vrefAdr                = 0xF075

  # TODO A estas direcciones de RAM deben asignarse direcciones virtuales :
  _tapStatus = CardParameter(tapStatusAdr , '<B', u'Tap Activo')
  _tapsFlags = CardParameter(0xE076, '<B', u'Tap Flags')

  # Palabra Clave para activar el control remoto :
  PASSWORD  = "CFG_USER"
  CLR_PSW   = "--------"
  _password = CardParameter(paswordAdr, '<8s', u'Clave de Configuración',
                                                                     'volatil')

  # Tiempos de Encendido y Apagado :
  _underVoltageTurnOn  = CardParameter(underVoltageTurnOnAdr ,
                                 '<H', u'Tiempo de Encendido desde Subtensión')
  _overVoltageTurnOn   = CardParameter(overVoltageTurnOnAdr  ,
                               '<H', u'Tiempo de Encendido desde Sobretensión')
  _underVoltageTurnOff = CardParameter(underVoltageTurnOffAdr,
                                     '<H', u'Tiempo de Apagado por Subtensión')
  _overVoltageTurnOff  = CardParameter(overVoltageTurnOffAdr ,
                                   '<H', u'Tiempo de Apagado por Sobretensión')

  # Rango de Taps Operativos :
  _tapsOpRange = CardParameter(tapsOpRangeAdr, '<B', u'Taps Utilizados')

  # Modo de Operación :
  _modeFunctions = CardParameter(modeFunAdr, '<B', u'Modo de Operación')

  # Umbrales de Tensión :
  _threshold = CardParameter(thresholdsAdr , '<24H' , u'Umbrales de Tensión')

  # Información de la tarjeta :
  _client = CardParameter(clientAdr, '<18s', u'Nombre del Cliente')
  _date   = CardParameter(dateAdr  , '<10s', u'Fecha de Producción')
  _serie  = CardParameter(serieAdr , '<7s' , u'Número de Serie')
  _vin    = CardParameter(vinAdr   , '<7s' , u'Tensión de Entrada')
  _vout   = CardParameter(voutAdr  , '<7s' , u'Tensión de Salida')
  _reg    = CardParameter(regAdr   , '<6s' , u'Regulación')
  _rs     = CardParameter(rsAdr    , '<5s' , u'Resistensia Serie')
  _rd     = CardParameter(rdAdr    , '<5s' , u'Resistecia de Divisor')
  _vref   = CardParameter(vrefAdr  , '<6s' , u'Tensión de Referencia')

  # Se define el registro de las mediciones 'instantáneas' :
  _measure_record = CardParameter(measureAdr, '<BHH', u'medición', 'volatil')

  # Se define la escala general de las mediciones :
  _scale = CardParameter(scaleAdr, '<16s', u'Escala de las mediciones')
  scale = ScaledParameter(_scale,
                           [lambda x: float(x.replace('\x00', ' ')),
                            lambda x : '%9.7f' %x],
                            fmt = r'%1.5f')

  _gainL = CardParameter(gainLAdr, '<H', u'Ganancia Fase L - Neutro')
  _gainU = CardParameter(gainUAdr, '<H', u'Ganancia Fase U - Neutro')
  _gainV = CardParameter(gainVAdr, '<B', u'Ganancia Fase V - Neutro')
  gainL  = ScaledParameter(_gainL,
                           [lambda x : math.sqrt(x/EstCard1V0.GAIN_NOM),
                            lambda x : x**2 * EstCard1V0.GAIN_NOM],
                            fmt = r'%7.5f [0x%04X]')

  # Factor de Normalización de la Ganancia :
  GAIN_NOM = 50362.0


  # Número de Taps Máximo de los modelos de Tarjeta :
  _TapLimit = {'EstCard 2V3'  : 5 , 'EstCard 5V1'  : 5, 'EstCard 13V1' : 6,
               'EstCard 23V0' : 10, 'EstCard 2V5-7tap' : 7,  'EstCard 18V0' : 8,
               'EstCard 24V0' : 6 , 'EstCard 20V1' : 8}

  # Contenido total de la EEPROM :
  _eepromLow  = CardParameter(eepromAdr, '<128B', 'Mitad baja de la EEPROM')
  _eepromHigh = CardParameter(eepromAdr+128, '<128B', 'Mitad alta de la EEPROM')

  def __init__(self, card) :
    # Se heredan las propiedades básicas de card (puerto serie, reporte e
    # identificación del software) ...
    self.dev = card.dev
    self.log = card.log
    self._id = card._id

    # Se registra el dispositivo como conocido :
    # TODO Debe verificarse el modelo de hardware  antes de validar isKnown
    self.isKnown = True

    # Se obtiene la identificación del Hardware :
    try :
      self.log.debug(u'Obteniendo la identificación del dispositivo remoto ...')

      _hardware_model    = CardParameter(HARDWARE_MODEL_ADR   ,
                               '<' + str(HARDWARE_MODEL_SIZE)    + 's',
                                         u'Modelo de Hardware'  ).__get__(self)
      _hardware_version  = CardParameter(HARDWARE_VERSION_ADR ,
                               '<' + str(HARDWARE_VERSION_SIZE)  + 's',
                                         u'Versión de Hardware' ).__get__(self)

    except OTCProtocolError as e:
            raise OTCProtocolError(u'No se pudo obtener la identificación '
                                                  u'del dispositivo.', e, self)

    strip = lambda s : s[:-1].strip() if s[-1] == '\x00' else  s.strip()

    self._id[u'hardware_model']   =  strip(_hardware_model)
    self._id[u'hardware_version'] =  strip(_hardware_version)

    # Se asignan los contenedores de los parámetros de cada fase de medición :
    self.LN = Phase(self, 'LN')
    self.UV = Phase(self, 'UV')

    # Se asignan las banderas de los funciones del modo de operación :
    self.modeFlags = ModeFlags(self)

    # Se asigna la clase de la representación interna de los factorees de
    # calibración :
    self.calibration_factor = CalibrationFactor1V0

    # Bandera para indicar si se esta en el modo remoto :
    self._remote_mode = False

    self.threshold = ThresholdSetFactory(self)

  # Salvo algunas excepciones, en general los parámetros del dispositivo y por
  # ende los atributos de EstCard, solo se leen o modifican una vez y resulta
  # conveniente identificarlos por su nombre 'natural' mas que por el nombre
  # formal del atributo que lo representa, con esta funcionalidad se incluyen
  # las funciones get() y set():
  def set(self, name, value) :
    # Los parámetros del dispositivo son de dos tipos ...
    # ModeFlags :
    try :
      # CardParameter ...
      if isAttributeName(name, type(self), CardParameter) :
        setattr(self,
                 getAttributeParameter(name, type(self), CardParameter), value)
      # o ModeFlags.Flag :
      elif isAttributeName(name, ModeFlags, ModeFlags.Flag) :
        setattr(self.modeFlags,
                 getAttributeParameter(name, ModeFlags, ModeFlags.Flag), value)
      else :
        raise ValueError(u'%s no es un parámetro de EstCard.')

    except struct.error as e :
       raise ValueError('Error : El valor no tiene el formato correcto.')


  def get(self, name) :
    if isAttributeName(name, type(self), CardParameter) :
      return getattr(self, getAttributeParameter(name, type(self), CardParameter))

    elif isAttributeName(name,  ModeFlags, ModeFlags.Flag) :
      return getattr(self.modeFlags,
                        getAttributeParameter(name, ModeFlags,  ModeFlags.Flag))

    else :
      raise ValueError(u'%s no es un parámetro de EstCard.')


  @property
  def eeprom(self) :
    contents = list(self._eepromLow)
    contents.extend(self._eepromHigh)
    return tuple(contents)


  # Número Máximo de la Tarjeta :
  @property
  def tapLimit(self):
    # TODO Si el modelo no esta registrado se produce una excepción.
    return self._TapLimit[self.id['hardware_model']]


  # Escala de la Medición
  @property
  def scale(self) :
    end = self._scale.find('\x00')
    if end < 0 : end = len(self._scale)
    return float(self._scale[:end])

  @scale.setter
  def scale(self, value) :
    self._scale = '%.9e\x00' % value


  # Métodos de Entrada y Salida del modo de configuración/calibración :
  def EnterRemoteMode(self) :
     self._password = EstCard1V0.PASSWORD
     self._mode = 0
     self._remote_mode = True

  def ExitRemoteMode(self) :
    if self._remote_mode :
      # CtrEst1V0, no responde correctamente al cierre de la configuración,
      # No existe razón para informar al usuario del error.
      report.consoleSetLevel(logging.CRITICAL)
      try :
        self._password = EstCard1V0.CLR_PSW
      except :
        pass
      report.consoleSetLevel(logging.ERROR)
      self._remote_mode = False


  # Métodos de Arranque y Detención de la captura de la medición :
  def StartMeasure(self, mode = 'L Cal') :
     if not math.isnan(self.scale) :
        # Se inicializa el hilo de ejecución para la medición :
        self.measure = MeasureTask(self)
        self.measure.setDaemon(True)
        self.LN.stats.arm()
        self.UV.stats.arm()
        self.measure.start()
        while not self.measure.started : continue
     else :
        raise ValueError(u'Error : No se puede proseguir, '
                                               u'la escala es inválida (NAN).')

  def StopMeasure(self) :
     # Se detiene el hilo de ejecución de la medición :
     if 'measure' in self.__dict__.keys() :
        self.measure.stop()
        while self.measure.is_alive() : continue


  def calibrator(self, input, ref):
    class Calibrator(object) :
      def __init__(self, card, input, ref) :
        self.input = input
        self.card = card

        self.old = self.card.calibration_factor(input, internal =
                             card.get('Ganancia Fase %s - Neutro' %self.input))

        rms = self.card.LN.rms if input == 'L' else self.card.UV.rms
        print 'rms : ', rms
        print 'ref : ', ref
        print 'self.old.bin : ', self.old.internal
        self.new = self.card.calibration_factor(input, effective = rms/ ref *
                                                             self.old.effective)
        #* \ self.old.internal)

      def commit(self):
        self.card.set('Ganancia Fase %s - Neutro' %self.input, self.new.internal)


    if not input in self.inputs_available() :
      raise ValueError(u'%s no es una entrada admisible.' %input)

    return Calibrator(self, input, ref)


  def inputs_available(self):
    if self.id['hardware_model'] in ['EstCard 23V0'] :
      return ['L','U']
    return ['L', 'U', 'V']


  # Fin de la Comunicación con el dispositivo :
  def close(self) :
    try :
      self.StopMeasure()
      super(type(self),self).close()

      self.ExitRemoteMode()
    except OTCProtocolError as e :
      pass


class CalibrationFactor1V2(CalibrationFactor1V0) :
  def __init__(self, input, **kwargs):
    self.input = input

    if (len(kwargs) == 1) and (kwargs.keys()[0] == 'internal') :
      self._bin = kwargs['internal']

    elif (len(kwargs) == 1) and (kwargs.keys()[0] == 'effective') :
      self._bin = (kwargs['effective']**2)*EstCard1V0.GAIN_NOM

    else :
      raise ValueError('CalibratorFactor debe invocarse definiendo solo uno de'
                       ' los siguientes argumentos explicitos : effective = '
                       '... o internal = ...')

    if self._bin > 65535 :
      raise ValueError('Error - El factor de calibracion (%f) excede el '
                       'rango.' % self._bin)

  @property
  def effective(self):
    return math.sqrt(self._bin/EstCard1V0.GAIN_NOM)


# Clase para el modelo de la tarjeta EstCard 1V2, se diferencicia de la primera
# por controlar el modo de medición de las entradas de tensión, durante la
# calbración.
class EstCard1V2(EstCard1V0) :
  u'''
  Clase para representar el modelo de la tarjeta EstCard 1V0 :
  '''

  # En este modelo la ganancia de la entrada V es de 16 bits.
  _gainV = CardParameter(EstCard1V0.gainVAdr, '<H',u'Ganancia Fase V - Neutro')

  # En este modelo se define el Modo de Medición :
  measureModeAdr = 0xE000
  _measureMode   = CardParameter(measureModeAdr , '<B', u'Modo de Medición',
                                                                     'volatil')
  def __init__(self, card) :
    super(EstCard1V0, self).__init__(self, card)

    # La versión 1V2 cambia la intrepretación del factor de calibración
    # (particularmente de la entrada V) :
    self.calibration_factor = CalibrationFactor1V2


  @property
  def measureMode(self) :
    return ['L Cal', 'U Cal', 'V Cal'][self._measureMode]

  @measureMode.setter
  def measureMode(self, value) :
    if value == 'L Cal' :
      # Medición de trabajo (aka,. L-N y U-V)
      self._measureMode = 0
    elif value == 'U Cal' :
      # Medición de trabajo (aka,. L-N y U-N, fuerza V = 0)
      self._measureMode = 1
    elif value == 'V Cal' :
      # Medición de trabajo (aka,. L-N y V-N, fuerza U = 0)
      self._measureMode = 2
    else :
      raise ValueError(u'Asignación del modo de medición '
                                                   u'con un valor incorrecto.')

  def StartMeasure(self, mode) :
    self.measureMode = mode
    EstCard1V0.StartMeasure(self)

  def ExitRemoteMode(self) :
    # CtrEst1V2, maneja correcamente el cierre del modo de configuración, al
    # contrario de su clase base, por lo tanto se sobrecarga este método,
    # para no deshabilitar el reporte de errores :
    if self._remote_mode :
      self._password = EstCard1V0.CLR_PSW
      self._remote_mode = False


# Clase Factoria, devuelve una instancia de la clase correspondiente al modelo
# (de software) de la tarjeta (i.e. EstCar1V0, EstCard1V2, etc.).
# El modelo de la tarjeta es obtenido al iniciar la comunicación con el dipo-
# sitivo (vía el puerto serie asignado) y  solicitarselo. Si el modelo no es
# reconocido devuelve simplemente una instancia de la clase base (OTCCard).
class EstCard(OTCCard) :
  def __new__(self, comm_name, throughput_limit = False) :
    # Se crea una instancia de la clase base (OTCCard) con el fin de obtener
    # laidentificación del software :
    card = OTCCard(OTCProtocol(comm_name, throughput_limit),
                                                  report.getLogger(u'EstCard'))

    # Se identifica el núcleo de software de tarjeta y se devuelve una
    # instancia para la versión correspondiente :
    if card.id['software_kernel'] == 'CtrEst 1V0' :
      card.log.debug(u'Núcleo de Software reconocido :%s' %
                                                    card.id['software_kernel'])
      return  EstCard1V0(card)

    elif card.id['software_kernel'] == 'CtrEst 1V2' :
      card.log.debug(u'Núcleo de Software reconocido :%s' %
                                                    card.id['software_kernel'])
      return  EstCard1V2(card)

    # Si el núcleo de software no es reconocido se devuelve la instancia de la
    # clase base, nótese hardware_model y hardware_versión han sido previamente
    # definidos durante su creación como 'unknown' :
    card.log.debug(u'Núcleo de Software no reconocido :%s' %
                                                    card.id['software_kernel'])
    return card

