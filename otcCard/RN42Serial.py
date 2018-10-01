#!/usr/bin/python
# -*- coding: utf-8 -*-

# RN42Serial.py

"""
  Define la clase RN42Serial para dar soporte en Android a los adaptadores del
  puerto serial sobre bluetooth con el radio RN42 de Roving/Microchip.

  La clase se define para ser compatible con la clase serial.Serial del paquete
  PySerial, aunque (mayormente por limitaciones de la pila Bluetooth del RN42)
  solo se soportan los siguientes métodos :

  Métodos soportados :
     open      : Abre el puerto con los ajustes especificados. Al contrario
                 de los puertos serie estándares, no es necesario haber
                 especificado el puerto (aka. la dirección bluetooth), en este
                 caso se aprovecha que el dispositivo Android, despliega la
                 lista de dispositivos bluetooth conectables, del cual
                 seleccionar el módulo a conectar.
     read      : Lectura de los caracteres recibidos en la linea RX del módulo.
     write     : Ordena la trasmisión de los caracteres dados por la línea TX
                 del módulo.
     flushInput: Elimina los caracteres pendientes de lectura.
     flushOutut: Solo espera determinado tiempo esperando optimistamente que
                 los caracteres hayan sido trasmitidos.

  Propiedades (ajustes) soportados :
     port       : Dirección Bluetooth del módulo.
     name       : Nombre del dispositivo Bluetooth.
     baudrate   : Velocidad de Comunicación.
     parity     : Paridad

  Propiedades parcialmente soportadas o ignoradas :
    timeout          : Tiempo de espera máximo para la recepción de caracteres,
                       el límite no se aplica a la trasmisión.
    writeTimeout,    : Ignorados, se permite su modificación pero no tiene
    interCharTimeout   efectos prácticos.

  Ciertos atributos no pueden modificarse, si se intenta se levanta una
  excepción :
     bytesize   : El número de bits por carácter es fijo e igual a 8.
                  A la verión de firmaware 6.15 del módulo, no responde a la
                  orden S7, la que permitiría seleccionar entre 7 y 8 bits.
     stopbits   : El número de bits de parada es fijo e igual a 1.
                  Aunque el módulo responde a la orden Q, que permite (entre
                  otros) seleccionar 1 o 2 bits de parada, su uso esta ligado
                  con un registro de depuración y su modificación a otro
                  valor diferente de 0, causa problemas de conexión.
     xonxoff,   : La funcionalidad que representan no esta habilitada,
     rtscts,      (su valor asignado es None).
     dsrdtr


  Los métodos de la clase Serial que no se incluyen son :
     setBreak   : El módulo debería enviar la señal break por medio de la
     sendBreak    orden SB, pero no la reconoce.
     setRTS     : Ni el control de flujo por hardware , ni el de software
     setDTR,      están implementados.
     setXON,
     getCD,
     getRI,
     getCTS,
     getDSR,
     setRtsToggle,
     getRtsToggle
     setBufferSize : La clase no incluye memoria intermedia.
     outWaiting
     inWaiting

  Las propiedades BAUDRATES, PARITIES, STOPBITS y BREAKLENGTH definen las
  capacidades del módulo en velocidad, paridad, bits de parada y duración
  de la señal break (aunque no sean realizables.)


  Comentario sobre la implementación :
    Para re-configurar el módulo es necesario cerrar la conexión, debido a que
    se utiliza el modo 'fast data' (F,1), para evitar que la escritura cause
    una entrada accidental en el modo de configuración.

    Nótese que per se la clase no altera ninguno de los ajustes del módulo, ni
    siquiera la velocidad o paridad, las que se ajustan temporalmente (por
    medio de la orden U,...).

    Los métodos actuales solo vacían la cola de recepción, la eliminación de
    la cola de trasmisión utiliza un criterio optimista, esperando un tiempo
    prudencial para que todos los caracteres hayan sido trasmitidos.

    No se implementa el límite de tiempo para las operaciones de escritura,
    aunque los métodos son aceptados, por razones de compatibilidad no tienen
    efectos prácticos.

    No se implementa ningún control de flujo, ni por hardware ni por software.

    El control de flujo por software es realizable, pero deberían utilizarse
    memorias de contención e hilos de ejecución paralelos para la recepción y
    trasmisión, quedando pendiente para una expansión futura del módulo.

    El control de flujo por hardware no es soportado por la fachada Bluetooth,
    no queda claro si cuando se activa en el módulo, pueden todavía ser leídas
    por las ordenes de lectura GPIO. De ser el caso, implica mantener la
    capacidad de ingresar al modo de configuración, con el inconveniente que
    escritura deben ser interpretadas para evitar la entrada accidental en
    este modo.

    Interpretar la escritura para eliminar el efecto de la secuencia '$$$'
    podría llevarse a cabo simplemente permitiendo que entre en el modo de
    configuración y luego utilizar la orden 'P' para pasar los caracteres,
    desafortunadamente esta no es (tampoco) funcional, lo que lleva a un
    camino cerrado, salvo se presente alguna alternativa.


  Observaciones al Módulo RN-42 :
    Las siguientes ordenes no son reconocidas (responde ERR, con los argumentos
    especificados) :
      S7 , ajuste del número de bits.
      SB , generación de la señal break.

    La orden de 'reboot' por software tiene una interacción desafortunada con
    la pila bluetooth, que impide la re-conexión del módulo con seguridad, por
    intervalos aleatorios.

    Luego de la orden de 'reboot' por software (R,1), ocasionalmente no se
    puede re-conectar el módulo, en ciertos casos el fenómeno es temporal,
    en otros caso parece necesitar un ciclo de apagado/encendido para recuperar
    su re-conectabilidad.

  Observaciones a la Fachada Bluetooth :
    El parámetro opcional Connection_id resulta siendo necesario para evitar
    la inconsistencia ocasional del API, cuando se pierde la conexión y se
    inicia una nueva (al parecer por defecto asume el id de la anterior).

"""

import android
import time

PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'
STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)
FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS = (5, 6, 7, 8)

PARITY_NAMES = {
    PARITY_NONE:  'None',
    PARITY_EVEN:  'Even',
    PARITY_ODD:   'Odd',
    PARITY_MARK:  'Mark',
    PARITY_SPACE: 'Space',
}

class RN42Serial(object) :
  # Las características del módulo no soporta todas las definidas en la clase
  # base y es necesario redefinirlas :
  BAUDRATES = (1200, 2400, 4800, 9600, 19200, 28800, 38400,
                                       57600, 115200, 230400, 460800, 921600)
  BAUDRATE_STR = ('1200', '2400', '4800', '9600', '19.2', '28.8',
                              '38.4', '57.6', '115K', '230K', '460K', '921K')
  BYTESIZES = (EIGHTBITS,) # (SEVENBITS, EIGHTBITS)
  PARITIES  = (PARITY_NONE, PARITY_EVEN, PARITY_ODD)
  STOPBITS  = (STOPBITS_ONE,) #(STOPBITS_ONE, STOPBITS_TWO)

  # Se definen las duraciones de la señal break según su hoja de especifica-
  # ciones, aunque realmente no las soporta :
  BREAKLENGTH = (37, 18.5, 12, 9, 7, 6) # mS.

  CONFIGURATION_DETECTION_CHAR = '$'

  # Android UUID del perfil SPP :
  UUID = '00001101-0000-1000-8000-00805F9B34FB'

  # Dispositivo de pruebas :
  UDT = '00:06:66:62:AF:C3'

  _droid = android.Android()


  def __init__(self,
               port = None,           # number of device, numbering starts at
                                      # zero. if everything fails, the user
                                      # can specify a device string, note
                                      # that this isn't portable anymore
                                      # port will be opened if one is specified
               baudrate= 9600,        # baud rate
               bytesize=EIGHTBITS,    # number of data bits
               parity=PARITY_NONE,    # enable parity checking
               stopbits=STOPBITS_ONE, # number of stop bits
               timeout=None,          # set a timeout value, None to wait forever
               xonxoff=False,         # enable software flow control
               rtscts=False,          # enable RTS/CTS flow control
               writeTimeout=None,     # set a timeout for writes
               dsrdtr=False,          # None: use rtscts setting, dsrdtr override if True or False
               interCharTimeout=None  # Inter-character timeout, None to disable
               ):
      """Initialize comm port object. If a port is given, then the port will be
         opened immediately. Otherwise a Serial port object in closed state
         is returned."""

      self._connID   = None
      self._port     = None           # correct value is assigned below through properties
      self._baudrate = None           # correct value is assigned below through properties
      self._bytesize = None           # correct value is assigned below through properties
      self._parity   = None           # correct value is assigned below through properties
      self._stopbits = None           # correct value is assigned below through properties
      self._timeout  = None           # correct value is assigned below through properties
      self._writeTimeout = None       # correct value is assigned below through properties
      self._xonxoff  = None           # correct value is assigned below through properties
      self._rtscts   = None           # correct value is assigned below through properties
      self._dsrdtr   = None           # correct value is assigned below through properties
      self._interCharTimeout = None   # correct value is assigned below through properties

      # assign values using get/set methods using the properties feature
      self.port     = port
      self.baudrate = baudrate
      self.bytesize = bytesize
      self.parity   = parity
      self.stopbits = stopbits
      self.timeout  = timeout
      self.writeTimeout = writeTimeout
      self.xonxoff  = xonxoff
      self.rtscts   = rtscts
      self.dsrdtr   = dsrdtr
      self.interCharTimeout = interCharTimeout

      if port is not None:
          self.open()


  def isOpen(self):
      """Check if the port is opened."""
      return self._connID is not None


  @property
  def port(self) :
    return self._port

  @port.setter
  def port(self, value) :
    was_open = self.isOpen()
    if was_open : self.close()

    self._port = value

    if was_open :
       self.open()


  @property
  def baudrate(self) :
    return self._baudrate

  @baudrate.setter
  def baudrate(self, value) :
    if value in RN42Serial.BAUDRATE_STR :
       value = RN42Serial.BAUDRATES[RN42Serial.BAUDRATE_STR.index(value)]

    elif not value in RN42Serial.BAUDRATES :
       raise ValueError(u"Not a valid baudrate: %r" % (value,))

    self._baudrate = value
    if self.isOpen() :  self._reconfigurePort()


  @property
  def bytesize(self) :
    return self._bytesize

  @bytesize.setter
  def bytesize(self, value) :
    if value != EIGHTBITS :
      raise ValueError(u"Not a valid byte size: %r" % (value,))


  @property
  def parity(self) :
    return self._parity

  @parity.setter
  def parity(self, value) :
    if not value in RN42Serial.PARITIES :
      raise ValueError(u"Not a valid parity: %r" % (value,))

    self._parity = value
    if self.isOpen() :  self._reconfigurePort()


  @property
  def stopbits(self) :
    return self._stopbits

  @stopbits.setter
  def stopbits(self, value) :
    if value != STOPBITS_ONE :
       raise ValueError(u"Not a valid stop bit size: %r" % (value,))


  @property
  def timeout(self) :
    return self._timeout

  @timeout.setter
  def timeout(self, value) :
    if value is not None:
      try:
        value + 1     # test if it's a number, will throw a TypeError if not...
      except TypeError:
        raise ValueError(u"Not a valid timeout: %r" % (value,))

      if value < 0: raise ValueError(u"Not a valid timeout: %r" % (value,))

      self._timeout = value


  @property
  def writeTimeout(self) :
    return self._writeTimeout

  @writeTimeout.setter
  def writeTimeout(self, value) :
    if value is not None:
      try:
        value + 1     # test if it's a number, will throw a TypeError if not...
      except TypeError:
        raise ValueError(u"Not a valid writeTimeout: %r" % (value,))

      if value < 0: raise ValueError(u"Not a valid writeTimeout: %r" % (value,))

      self._writeTimeout = value


  @property
  def xonxoff(self) :
    return self._xonxoff

  @xonxoff.setter
  def xonxoff(self, value) :
    if value :
       raise ValueError(u'XON/XOFF Flow Control is not supported')


  @property
  def rtscts(self) :
    return self._rtscts

  @rtscts.setter
  def rtscts(self, value) :
    if value :
       raise ValueError(u'RTC/CTS Flow Control is not supported')


  @property
  def dsrdtr(self) :
    return self._dsrdtr

  @dsrdtr.setter
  def dsrdtr(self, value) :
    if value :
       raise ValueError(u'DSR/DTR Flow Control is not supported')


  @property
  def interCharTimeout(self) :
    return self._interCharTimeout

  @interCharTimeout.setter
  def interCharTimeout(self, value) :
    if value is not None:
      try:
        value + 1     # test if it's a number, will throw a TypeError if not...
      except TypeError:
        raise ValueError(u"Not a valid interCharTimeout: %r" % (value,))

      if value < 0: raise ValueError(u"Not a valid interCharTimeout: %r" % (value,))

      self._interCharTimeout = value


  def __repr__(self):
    """String representation of the current port settings and its state."""
    return "%s<id=0x%x, open=%s>(port=%r, baudrate=%r, bytesize=%r, parity=%r, stopbits=%r, timeout=%r, xonxoff=%r, rtscts=%r, dsrdtr=%r)" % (
       self.__class__.__name__,
       id(self),
       self._isOpen,
       self.portstr,
       self.baudrate,
       self.bytesize,
       self.parity,
       self.stopbits,
       self.timeout,
       self.xonxoff,
       self.rtscts,
       self.dsrdtr,
    )


  def close(self):
    """close port"""
    if self._connID is not None :
        self._droid.bluetoothStop(self._connID)
        self._connID = None


  def _read(self, size = 1) :
    import base64
    ans = self._droid.bluetoothReadReady(self._connID)

    if ans.result :
      ans = self._droid.bluetoothReadBinary(size, self._connID)

    if ans.error :
      raise self.exception(u'Se perdió la comunicación')

    if ans.result :
     #return [ord(b) for b in base64.b64decode(ans.result)]
     return base64.b64decode(ans.result)
    else :
      return []


  def read(self, size=1):
    """Read size bytes from the serial port. If a timeout is set it may
    return less characters as requested. With no timeout it will block
    until the requested number of bytes is read."""
    if self._connID is None : raise portNotOpenError

    read = bytearray()
    for i in range(size) :
      if self.timeout > 0 :
        timeout = 0
        while timeout <= self.timeout :
          data = self._read(size - len(read))
          if len(data) > 0 : break

          time.sleep(0.01)
          timeout += 0.01

      else :
        data = self._read(size)

      if len(data) > 0 :
         try :
           read.extend(data)
         except Exception as e :
           print 'type = ', type(data)
           print 'data = ', data
           raise e
      elif self.timeout :
        break

    return bytes(read)


  def write(self, data):
    """Output the given string over the serial port."""
    import base64

    if self._connID is None :
      raise self.exception('Attempting to use a port that is not open')

    ans = self._droid.bluetoothWriteBinary(base64.b64encode(data), self._connID)

    if ans.error :
      print ans.error
      raise self.exception(u'Se perdio la comunicacion (%s)' % ans.error)

  def flushInput(self):
    """Clear input buffer, discarding all that is in the buffer."""
    if self._connID is None :
      raise self.exception('Attempting to use a port that is not open')

    while self._read() : pass


  def flushOutut(self) :
    import time
    time.sleep(0.5)


  def open(self, strict = False) :
    """Open port with current settings. This may throw a SerialCommException
       if the port cannot be opened."""
    if self._connID is not None :
      raise self.exception("Port is already open.")

    if strict and (self._port is None) :
      raise self.exception(u"Bluetooth Address must be configured before it can be used.")

    if self._port is None :
      id, result, error = self._droid.bluetoothConnect(self.UUID)
    else :
      id, result, error = self._droid.bluetoothConnect(self.UUID, self._port)

    if error :
      raise self.exception("Connection failed.")

    self._connID = result

    # Si el puerto fue seleccionado por el usuario, se debe obtener la 
    # dirección Bluetooth del dispositivo seleccionado :
    if self._port is None :
       self.write('GB\r')
       self._port = self.read(19)[:-2]
       print 'Bluetooth Address = ', self.port
       print self._port
       
    # Como el módulo RN42, no soporta en los hechos, ni control de flujo, ni
    # diferentes números de bits de datos o parada, la configuración es real-
    # mente simple, ingresando al modo de configuración :
    self.write(3*self.CONFIGURATION_DETECTION_CHAR)
    if self.read(5) != 'CMD\r\n' :
      raise self.exception(u"El módulo rechaza entrar en el modo de configuración.")

    # para definir la velocidad y paridad, con el modo de conexión 'fast data' :
    self.write('U,%s,%s\r' %
                 (self.BAUDRATE_STR[self.BAUDRATES.index(self._baudrate)],
                 ('N','E','O')[self.PARITIES.index(self._parity)]) )

    # Se lee la respuesta :
    if self.read(5) != 'AOK\r\n' :
      raise self.exception(u"El módulo rechaza entrar en el modo 'data fast'.")

    self.write(3*self.CONFIGURATION_DETECTION_CHAR)
    if self.read(5) != 'CMD\r\n' :
      raise self.exception(u"El módulo rechaza entrar en el modo de configuración.")

    # para definir la velocidad y paridad, con el modo de conexión 'fast data' :
    self.write('F,1\r')


  def _reconfigurePort(self) :
    # Esta función se invoca cuando un ajuste se ha cambiado, solo realiza una
    # función si el módulo esta conectado :
    if self._connID is not None :
      # Como se utiliza el 'Fast Mode', no es posible entrar en el modo de
      # configuración, sin cerrar ... 
      port = self._port
      self.close()
      # y re-abrir la conexión con el módulo Bluetooth, el cambio de
      # configuración lo realiza entonces la función open() :
      self.open(port)


  @staticmethod
  def exception(msg) :
    return IOError(msg)


if __name__ =='__main__' :
   from time import sleep
   
   print 'Creando ...'
   dev = RN42Serial()
   
   print 'Asignando Port ...'
   dev.port = '00:06:66:62:AF:C3'
   dev.timeout = 0.5
   dev.baudrate =57600
   
   print 'Abriendo ...'
   dev.open()
   
   print 'Conecatado a : ', 
   
   print 'Trasmitiendo...'
   for i in range(500) :
      dev.write('GG')
      print 'GG',
      sleep(0.050)
      
   print '\nCerrando ...'
   dev.close()

