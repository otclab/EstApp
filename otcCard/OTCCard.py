#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Oscar'

from otcCard.ext_struct import ext_struct
from weakref import WeakKeyDictionary
from otcCard.OTCProtocol import *
import logging

# Direcciones de las cadenas de identificación del Modelo/Versión
HARDWARE_MODEL_ADR     = 0x0000
HARDWARE_VERSION_ADR   = 0x0012
SOFTWARE_KERNEL_ADR    = 0x0024
SOFTWARE_VERSION_ADR   = 0x0036
SOFTWARE_REVISION_ADR  = 0x0048
PRODUCTION_DATE_ADR    = 0x005A

HARDWARE_MODEL_SIZE    = 0x0012
HARDWARE_VERSION_SIZE  = 0x0012
SOFTWARE_KERNEL_SIZE   = 0x0012
SOFTWARE_RELEASE_SIZE  = 0x0012
SOFTWARE_REVISION_SIZE = 0x0012
PRODUCTION_DATE_SIZE   = 0x0006


class OTCCard(object) :
  u'''
  Clase base para los dispositivos que utilizan el protocolo OTCProtocol,
  garantiza que los dispositivos tengan los atributos :
     dev : interfaz operando el protocolo OTCProtocol es decir es una
           instancia de la clase OTCProtocol.
     log : Sistema de reporte estándar es decir del tipo logging.Logger
     id  : Identificación del hardware y software de la tarjeta.

  La creación de una instancia inicia la comunicación con el dispositivo
  (en el puerto dev) y la obtención de la identificación del hardware y
  software (nombre/kernel, versión y revisión).
  '''
  def __init__(self, dev, log, ) :
    if not isinstance(dev, OTCProtocol) :
       raise ValueError(u'El primer argumento debe ser del tipo OTCProtocol.')
    self.dev = dev

    if not isinstance(log, logging.Logger) :
      raise ValueError(u'El segundo argumento debe ser '
                                                   'del tipo logging.Logger.')
    self.log = log

    try :
      self.log.debug(u'Obteniendo la identificación del dispositivo remoto ...')

      _hardware_model    = CardParameter(HARDWARE_MODEL_ADR   ,
                               '<' + str(HARDWARE_MODEL_SIZE)    + 's',
                                         u'Modelo de Hardware'  ).__get__(self)
      _hardware_version  = CardParameter(HARDWARE_VERSION_ADR ,
                               '<' + str(HARDWARE_VERSION_SIZE)  + 's',
                                         u'Versión de Hardware' ).__get__(self)

      _software_kernel   = CardParameter(SOFTWARE_KERNEL_ADR  ,
                 '<' + str(SOFTWARE_KERNEL_SIZE)   + 's', u'Modelo de Software'  ).__get__(self)
      _software_release  = CardParameter(SOFTWARE_VERSION_ADR ,
                 '<' + str(SOFTWARE_RELEASE_SIZE)  + 's', u'Versión del Software' ).__get__(self)
      _software_revision = CardParameter(SOFTWARE_REVISION_ADR,
                 '<' + str(SOFTWARE_REVISION_SIZE) + 's', u'Revisión del Software').__get__(self)

      #_production_date = CardParameter(PRODUCTION_DATE_ADR  ,
      #          '<' + PRODUCTION_DATE_SIZE   *'s', u'Fecha de Producción' )

      self._id = { u'hardware_model'    : _hardware_model    ,
                   u'hardware_version'  : _hardware_version  ,
                   u'software_kernel'   : _software_kernel   ,
                   u'software_release'  : _software_release  ,
                   u'software_revision' : _software_revision  }

    except OTCProtocolError as e:
      raise OTCProtocolError(u'No se pudo obtener la identificación '
                                                 u'del dispositivo.', e, self)

    # En este punto, solo se ha identificado el núcleo de software del
    # dispositivo y se desconoce el hardware (que deberá reconocerse en las
    # subclases) :
    self.isKnown = False


  def get_id(self) :
    return self._id

  id = property(get_id, None, None, "Identificación del dispositivo.")


  def close(self) :
    self.dev.close()


class CardParameter(object) :
  u"""
  Clase para encapsular los parámetros de un dispositivo remoto, comunicado
  por medio del protocolo OTCProtocol, formalmente es una clase del tipo des-
  criptor' de manera que su valor pueda ser manipulado como una variable es-
  tándar.

  Los parámetros son básicamente secuencias de bytes que tienen asociadas un
  nombre, una dirección, un formato y un tipo, los cuales son definidos al
  crear sus instancias.

  Como una clase del tipo descriptor (i.e. una clase con los métodos _get__
  y/o __set__), sus instancias deben pertenecer a una CLASE para operar como
  se espera (y no a una instancia de una clase, aunque python no impide su
  acceso desde estas). La instancia de esta CLASE debe ser o contener un
  atributo denomindo card, que debe ser una subclase de OTCCard.

  El nombre se utiliza para propósitos administrativos durante el reporte de
  depuración, el formato especifica la forma como se interpreta la secuencia
  de bytes, en una lista de valores 'elementales' i.e. byte, word, cadenas de
  caracteres y/o secuencia de bytes y por ende su tamaño i.e. la longitud de
  la secuencia de bytes. Finalmente el tipo identifica su volatilidad, es
  decir si es necesario leerlo cada vez o puede utilizarse una memoria espejo
  para almacenar su valor y evitar el uso del interfaz de comunicación cada
  vez que se solicite su valor.

  Por razones de flexibilidad el formato del parámetro (fmt) que permite
  identificar sus componentes sigue las mismas reglas que las del módulo
  'struct'. Salvo 4 excepciones, si se especifica fmt como :
    'byte' : Identifica un entero en el rango de 0 a 255, aka. BYTE
             también es equivalente al formato '<B'.
    'word' : Identifica un entero en el rango de 0 a 65535, aka. WORD
             o unsigned int, también es equivalente al formato '<H'.
  por otro lado el carácter de formato 's' tiene el mismo uso para
  identificar cadenas de caracteres, sin embargo la cadena se trunca
  hasta el primer carácter NUL ('\x00'). Finalmente se introduce el carácter
  de formato 'S' por el cual se identifica el componente como una secuencia
  (lista) de bytes (de la longitud especificada por el numeral que lo precede).
  """
  # TODO Revisar los formatos byte, word y S
  def __init__(self, adr, fmt, name, typ = 'normal') :
    self.adr = adr
    self.name = name

    # El atributo value se utiliza para memorizar el último valor leído o
    # escrito. A diferencia de los otros atributos depende de la instancia
    # (card) y no a la clase en que esta definido este descriptor. Resulta
    # natural utilizar un diccionario para mantener la correspondencia entre
    # la instancia y value. Por otro lado, si la instancia es desechada no
    # es necesario mantenerla (ni obstruir el trabajo de colector de desechos)
    # por lo que se utiliza WeakKeyDictionary :
    self.value = dict() #WeakKeyDictionary()

    # se reconocen los formatos específicos 'byte' y 'word'
    if fmt in ['byte', 'uint8_t'] :
      fmt = '<B'

    elif fmt in ['word', 'uint16_t'] :
      fmt = '<H'

    elif fmt in ['uint24_t'] :
      fmt = '<G'

    elif fmt in ['int24_t'] :
      fmt = '<g'

    elif fmt in ['dword', 'uint32_t'] :
      fmt = '<L'

    elif fmt in ['int32_t'] :
      fmt = '<l'

    elif fmt in ['uint40_t'] :
      fmt = '<J'

    elif fmt in ['int40_t'] :
      fmt = '<j'

    self.fmt = fmt

    # Se calcula el tamaño de la secuencia de bytes que representa el
    # parámetro :
    self.size = ext_struct.calcsize(fmt)


    if (typ == 'normal') or (typ == 'volatil') :
      self.typ = typ ;
    else :
      raise ValueError(u'RemoteParameter.__init__ : El valor ("%s") no '
                           u'es admisible para el argumento typ.' % str(typ))


  def __get__(self, instance, owner = None) :
    # Se verifica que instance sea o que contenga un atributo denominado card,
    # sea una instancia de la clase OTCCard :
    if isinstance(instance, OTCCard) :
      card = instance
    elif 'card' in instance.__dict__ :
      card = instance.card
    else :
      instance.log.exception(u'RemoteParameter.__get__ : '
             u'La instancia o su atributo card no es una subclase de OTCCard.')
      raise ValueError('La instancia o su atributo card no es una '
                                                        'subclase de OTCCard.')

    # La lectura desde el dispositivo es incondicional si es volátil o su valor
    # no se ha leído o escrito antes :
    try :
      if (self.typ != 'volatil') :
        return self.value[card]
    except :
      pass

    try :
      card.log.debug (u"Lectura del parámetro '%s' [0x%04X / 0x%02X]"
                                             %(self.name, self.adr, self.size))

      # Lectura del la secuencia de bytes del valor del parámetro :
      val = card.dev.getData(self.adr, self.size)

      # Para normalizar la identificación de los componentes del parámetro se
      # convierte en una cadena de caracteres ...
      #val = "".join(map(chr, val))
      card.log.debug (u"Valor del parámetro : <%s>" %repr(val))

      # Se decodifica el paquete de datos :
      val = ext_struct.unpack(self.fmt, val)

      # Por convención (y facilidad de uso) si el parámetro solo contiene un
      # solo elemento, se trabaja como una instancia simple, sino como una
      # tupla :
      if len(val) == 1 : val = val[0]

      # Se memoriza el último valor del parámetro (En razón de evitar el
      # uso del interfaz ante sub-siguientes operaciones de lectura) :
      self.value[card] = val

      return val

    except OTCProtocolError as e:
      self.value[card] = None
      raise OTCProtocolError( u'Fallo la lectura de "%s".' %self.name, e, card)

    except Exception as e:
      card.log.exception(u'RemoteParameter.__get__ : '
                    u'Fallo inesperado al leer el parámetro: "%s".', self.name)
      raise e


  def __set__(self, instance, *val) :
    # Se verifica que instance sea o que contenga un atributo denominado card,
    # sea una instancia de la clase OTCCard :
    if isinstance(instance, OTCCard) :
      card = instance
    elif 'card' in instance.__dict__ :
      card = instance.card
    else :
      instance.log.exception(u'RemoteParameter.__set__ : '
             u'La instancia o su atributo card no es una subclase de OTCCard.')
      raise ValueError('La instancia o su atributo card no es una '
                                                        'subclase de OTCCard.')

    card.log.debug (u"Escritura del parámetro '%s' [0x%04X / 0x%02X}" %
                                            (self.name, self.adr, self.size))

    # En general el argumento que contienen el valor del parámetro es una
    # tupla/lista o diccionario de sus elementos, no obstante por flexi-
    # bilidad cuando el parámetro en si consta de un solo elemento (i.e.
    # números enteros o cadenas de caracteres) se admite como argumento,
    # por lo que debe estandarizarse a una tupla para su procesamiento,
    # por otro lado cuando se invoca indirectamente por medio de setattr()
    # el argumento es pasado como una tupla de un único elemento el cual
    # es a su vez una lista o tupla de los argumentos, los cuales deben
    # extraerse :
    if isinstance(val, tuple) :
      if (len(val) == 1) and (type(val[0]) in [list, tuple]) :
        val = val[0]
    else :
      val = (val,)
      
    try :
      # Se codifica val en una cadena de caracteres :
      val_str = ext_struct.pack(self.fmt, *val)

      # Se actualiza el valor del parámetro en el dispositivo remoto,
      # en segmentos limitados  en las frontera de 16 bytes :
      substr_adr = self.adr
      while len(val_str) > 0 :
        substr_len = 16 - (substr_adr & 0x0F)
        card.dev.setData(substr_adr, val_str[0: substr_len])
        substr_adr += substr_len
        val_str = val_str[substr_len:]

      #for n in range(0, len(val_str), 16) :
      #   card.dev.setData(self.adr + n, val_str[n : n+16])

      # En este punto self.value es una tupla, tipo que es inconveniente cuando
      # solo existe un solo valor, y se requiere manipularlo directamente :
      if len(val) == 1 : val = val[0]

      # Se memoriza el último valor del parámetro (En razón de evitar el uso
      # del interfaz ante sub-siguientes operaciones de lectura) :
      self.value[card] = val

      card.log.debug (u"Escritura del parámetro '%s' exitosa." %self.name)
      return

    except OTCProtocolError as e:
      del self.value[card]
      raise OTCProtocolError(u'No se pudo modificar "%s".'%self.name, e, card)

    except Exception as e:
      card.log.exception(u'RemoteParameter.__set__ : '
                u'Fallo inesperado al modificar el parámetro : %s.'% self.name)
      raise e

  def __len__(self) :
    """
    Devuleve el tamaño en bytes del valor representado por CardParameter
    """
    return self.size

# TODO Agregar formato del valor escalado, con capacidad de representar el
# TODO Mejorar la redacción de __doc__
# escalado y -opcionalmente-  el interno.
class ScaledParameter(object) :
  u'''
  Encapsula un parámetro del tipo CardParameter, cuya representación natural
  es un número de punto flotante.

  Durante su creación se definen los siguientes parámetros :
    card_parameter  : El parámetro a encapsular, debe ser una instancia de
                      CardParameter.
    funs            : Es un lista de dos elementos, el primero es la función
                      de conversión del valor interno (remoto) a su
                      equivalencia en punto flotante.
                      El segundo elemento es la función inversa, i.e. la de
                      conversión del su equivalente en punto flotante a su
                      valor interno (remoto)
    limits          : Es un lista de dos elementos, el valor mínimo y máximo
                      respectivamente ( en ese orden) del valor interno a
                      excepción que el valor interno no sea numérico en cuyo
                      caso es el del valor equivalente en punto flotante.
    fmt             : Es la cadena de caracteres que sirve como patrón para
                      el método __str__. Si ...

  La clase es un descripor, de manera que pueda ser manipulada como una varia-
  ble, cuyo valor (principal) es una subcalse de los números de punto flotante
  (float), de manera que pueda ser manipulado como un valor númerico.

  La subclase de float, incluye el atributo internal para aceeder al valor al-
  macenado (en el dispositivo) y/o modificarlo directamente, , verificando que
  se encuentre en un rango determinado. Por defecto los límites son los de al
  representación binaria (del número de bytes del parámetro que encapsula) y
  pueden ser definidos explícitamente durante su creación por medio del
  argumento limits, el cual debe ser vector de dos números, respectivamente
  en el orden mínimo y  máximo valor válido.

  También sobrecarga la función __str__ para estandarizar su representación (la
  que puede incluir el valor interno) y que es definida durante su creación por
  medio del argumento fmt.

  Adicionalmente durante la creación de ScaledParameter se incluye el argumento
  card_parameter con el parámetro del tipo card_parameter a encapsular y el
  vector funs, con las funciones del valor natural en función del valor interno
  y viceverza la del valor interno en función del natural. Huelga mencionar
  que deben ser funciones inversas entre sí.

   El argumento fmt debe ser una cadena de caracteres, con hasta dos argumentos
   el primer de los cuales se asignara a la representación natural y la segunda
   a la interna. De lo contrario debe ser una función que acepte como único
   argumento la subclase de float y devuelva la cadena de caracteres
   respectiva.
  '''
  def __init__(self, card_parameter, funs, limits = None, fmt = None):
    self.card_parameter = card_parameter

    self.__funs = funs

    if not limits is None:
      self.limits = limits
    else :
      self.limits = [0, 256**(card_parameter.size)]

    if fmt ==  None :
      fmt = r'%6.2f [0x%0' + str(2*card_parameter.size) + 'X]'

    if fmt.count('%') == 1 :
      self.fmt = lambda x : fmt %x
    else :
      self.fmt = lambda x : fmt %(x, x.internal)


  def __set__(self, instance, value):
    value = self.__funs[1](value)

    if isinstance(value, (int, float)) :
      chk_value = value
    else :
      chk_value = self.__funs[0](value)

    if (chk_value < self.limits[0]) or (chk_value > self.limits[1]) :
      raise ValueError('Valor interno (%d) fuera de rango .' % chk_value)

    self.card_parameter.__set__(instance, value)


  def __get__(self, instance, owner):
    card_parameter = self.card_parameter
    remote_value = card_parameter.__get__(instance, owner)
    funs = self.__funs

    class __FloatParameter(float) :
      def __new__(cls, internal_value) :
        return float.__new__(cls, funs[0](internal_value))

      def __init__(this, internal_value) :
        this.internal_value = internal_value

      @property
      def internal(this):
        return this.internal_value

      @internal.setter
      def internal(this, value):
        if (value < self.limits[0]) or (value > self.limits[1]) :
          raise ValueError('Valor interno (%d) fuera de rango .' % value)
        card_parameter.__set__(instance, value)

      def ScaledBy(this, factor) :
        return this.__class__(funs[1](funs[0](this.internal)*factor))

      def __str__(this):
        return self.fmt(this)

    return __FloatParameter(remote_value)


