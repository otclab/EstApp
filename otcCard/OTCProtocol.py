#!/usr/bin/python
# -*- coding: utf-8 -*-

import struct
import sys
import threading
from time import sleep

import SerialDevice
import report


# Caracteres Especiales :

ESCAPE_CHAR = '\x1B'
EXIT_CHAR   = 'X'
GET_CHAR    = 'G'
SET_CHAR    = 'S'
ACK_CHAR    = '\x17'
NACK_CHAR   = '\x15'

SpecialChar = [ESCAPE_CHAR, EXIT_CHAR, GET_CHAR, SET_CHAR, ACK_CHAR, NACK_CHAR]


# TODO Remover
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


def com_list() : return SerialDevice.com_list()


class OTCProtocolError(Exception) :
   def __init__(self, msg, cause = None, obj = None) :
      self.msg = msg
      Exception.__init__(self, msg)

      if isinstance(cause, OTCProtocolError) :
         self.msg += u'\nrazón : %s' % cause.msg

      elif isinstance(cause, Exception) :
         self.msg += u'\nrazón : %s' % cause.message

      elif cause :
         self.msg += u'\nrazón : %s' % cause.__str__()

      if obj : obj.log.error(msg)
      
      self.message = self.msg


class OTCProtocol :
   u"""
   Protocolo de comunicaciones para micro-controladores con interfaz serie,
   adaptado para la lectura y escritura de su diferentes tipos de memoria.
   El espacio de memoria esta identificado por su dirección de 16 bits y
   puede ser del tipo RAM, FLASH o EEPROM, siendo responsabilidad del
   dispositivo realizar la asignación real de los espacios/tipos de
   memoria.
   """


   def __xmit(self, data) :
      u"""
      Transmite 'data'. Si no puede hacerlo dentro del límite de tiempo
      establecido (writeTimeout) aborta la operación por medio de una
      excepción (del tipo OTCProtocolError).
      """
      try :
         for d in data :
            self.log.debug(u'Trasmitiendo : 0x%02X' %ord(d))
            self.__comm.write(d)
            if self.throughput_limit :
               sleep(0.05)

      except SerialDevice.SerialTimeoutException as e:
         raise OTCProtocolError(u'Fallo de Transmisión (timeout).', e, self)


   def __rcve(self) :
      """
      Espera por la recepción de 1 byte desde el dispositivo.
      """
      self.log.debug('Recibiendo (1 byte) ...')
      byte = self.__comm.read(1)

      if (byte == '') or (byte is None) :
         raise OTCProtocolError(u'El dispositivo no responde (timeout).',
                                                                    None, self)

      self.log.debug(u'Se recibió : 0x%02X,' %(ord(byte)))

      return byte


   def __RcveAns(self) :
      u"""
      Recibe e identifica la respuesta del dispositivo, devuelve TRUE/FALSE
      según responda ACK_CHAR o NACK_CHAR respectivamente.
      Termina con una excepción si no se recibe una respuesta o no puede ser
      identificada.
      """
      try :
         self.log.debug(u'Recibiendo la respuesta (ACK/NACK) ...')
         ans = self.__rcve()
      except OTCProtocolError as e :
         raise OTCProtocolError(u'El dispositivo no envió '
                               u'la respuesta de aceptación/rechazo.', None, self)

      if  ans == NACK_CHAR :
         self.log.debug(u'Respuesta de Rechazo (NACK).')
         return False
      elif ans == ACK_CHAR :
         self.log.debug(u'Respuesta de aceptación (ACK).')
         return True

      raise OTCProtocolError( u'El dispositivo envió una '
                                         u'respuesta no reconocible.', None, self)


   def __RcveData(self, size) :
      u"""
      Recibe size bytes de datos y los devuelve. La secuencia de datos pueden
      incluir secuencias de escape (caso en el cual solo se considera en la
      cuenta como un dato, aún cuando su transmisión implica 2 bytes), la
      secuencia de bytes que representan los datos debe terminar con un byte
      de respuesta. Este último debe ser ACK_CHAR si se transmitieron los size
      datos o NACK si la transmisión es parcial o nula.
      Levanta una excepción si el dispositivo devuelve NACK_CHAR, o si la
      transmisión es parcial o nula (timeout) o se recibe una secuencia de
      escape inválida.
      """
      try :
         self.log.debug(u'Esperando la recepción de %d (data) bytes' % size)
         data = []
         for i in range(0, size) :
            data += self.__rcve()

            if data[i] == ESCAPE_CHAR :
               data[i] = chr(ord(self.__rcve()) ^ ord(ESCAPE_CHAR) ^ 0x55)

               if not (data[i] in SpecialChar) :
                  self.log.debug(u'Secuencia de escape desconocida '\
                                         u'ESC (0x1B) / 0x%02X' % ord(data[i]))
                  raise OTCProtocolError(u'Se recibio una secuencia '
                                          u'de escape desconocida', None, self)
               self.log.debug(u'Secuencia de escape identificada '
                                               u'para : 0x%02X' % ord(data[i]))

            elif data[i] == ACK_CHAR :
               raise OTCProtocolError(u'Se recibio ACK, truncando'
                              u' la recepción (%d en lugar de %d bytes).'
                                                   % ((i+1), size), None, self)

            elif data[i] == NACK_CHAR :
               raise OTCProtocolError(u'Se recibió (NACK), interrumpiendo'
                                u' la recepción (a %d en lugar de %d bytes).'
                                                   % ((i+1), size), None, self)

         if not self.__RcveAns() :
            raise OTCProtocolError(u'El dispositivo rechazo la lectura.',
                                                                    None, self)

         return map(ord, data)

      except OTCProtocolError as e :
         raise OTCProtocolError(u'Fallo la Recepcion.', e, self)


   def getData(self, adr, size) :
      u"""
      Lee size bytes desde la dirección adr en el dispositivo y los devuelve
      como una lista.
      """
      with self._lock :

         try :
            self.log.debug(u'Lectura del contenido de %d bytes desde 0x%04X.' \
                                                                  %(size, adr))

            # Limpia la memoria de contención de recepción :
            self.__comm.flushInput()

            # Envía el comando según el protocolo, nótese que se asegura la con-
            #versión a una secuencia de bytes de los parámetros importados :
            cmd = GET_CHAR + struct.pack('<H', adr) + struct.pack('<B', size)
            self.__xmit(cmd)

            # Se espera por la respuesta del comando :
            ans = self.__RcveData(size)

            return ans

         except OTCProtocolError as e :
            raise OTCProtocolError(u'No se pudo obtener el contenido de ' \
                               u'0x%04X / 0x%02X bytes.' %(adr, size), e, self)


   def setData(self, adr, data, mode = 'byte') :
      u"""
      Escribe el contenido de data desde la dirección adr en el dispositivo,
      Data puede ser una cadena de caracteres o una lista de bytes o un byte,
      o una palabra de 16 bits.
      En el caso de una cadena de caracteres o una lista de bytes el argumento
      mode es ignorado. Cuando data es un entero el parámetro mode controla
      si solo se consideran los primeros 8 bis (mode = 'byte') o los primeros
      16 bits (mode = 'word').
      La lista de bytes es en realidad una lista de enteros, el que solo se
      consideran válidos los bytes LSB de c/u.
      """
      with self._lock :
         try :
            if isinstance(data, str) :
               data_bytes = data
            elif isinstance(data, int) :
               if mode == 'byte' :
                  data_bytes = chr(data & 0xFF)
               elif mode == 'word' :
                  data_bytes = struct.pack('<H', data)
               else :
                  self.log.exception(u'SetData : Tercer argumento '
                                                           u'(mode) inválido.')
                  sys.exit()
            elif isinstance(data, list) :
               data_bytes = ""
               for item in data :
                  data_bytes += struct.pack('<B', item)
            else :
               raise ValueError(u'SetData : Primer argumento (data) no es '
                                 u'un tipo válido (str, int o list de int).\n')

         except Exception as e:
            self.log.exception(u'SetData : Fallo inesperado al interpretar '
                                                u'los argumentos, detalle :\n')
            raise e

         try :
            self.log.debug(u'Modificación del contenido de %d bytes '
                                      u'desde 0x%04X.' %(len(data_bytes), adr))

            # Limpia la memoria de contención de recepción :
            self.__comm.flushInput()

            # Envía el comando según el protocolo, nótese que se asegura la con-
            # versión a una secuencia de bytes de los parámetros importados :
            cmd = SET_CHAR + struct.pack('<H', adr) + struct.pack('B',
                                                               len(data_bytes))
            self.__xmit(cmd)

            # En este punto data_bytes puede contener los caracteres especiales
            # que deben ser substituidos por sus secuencias de escape ...
            for ch in SpecialChar :
               data_bytes = data_bytes.replace(ch,
                                           '\x1B' + chr(0x1B ^ ord(ch) ^ 0x55))
            # antes de enviarla :
            self.__xmit(data_bytes)

            # Se espera por la respuesta del comando :
            ans = self.__RcveAns()
            return ans

         except OTCProtocolError as e :
            raise OTCProtocolError(u'No se pudo modificar el contenido de '
                    u'0x%04X / 0x%02X bytes.' %(adr, len(data_bytes)), e, self)


   def close(self) :
      self.__comm.close()
      self.log.debug(u'Se cerro el puerto serie : %s', str(self.__comm.port))


   def __init__(self, comm_name, throughput_limit = False) :
      u"""
      Toma control del puerto serie comm_name e inicia la comunicación
      con el dispositivo remoto leyendo su identificación.
      """

      # Cuando comm_name es None, solo después de abrir el puerto (caso de 
      # puertos Bluetooth en Android) se puede nominar el manejador de
      # reportes, mientras tanto se asigna provicionalmente :
      self.log = report.report.getLogger(u'OTCProtocol.' + 
               (u'*OPPENING_IN_PROGRESS*' if comm_name is None else comm_name))

      # La instancia de la clase puede ser utilizada por mas de un hilo de 
      # ejecución, por lo que tanto se utiliza un objeto Lock(), para prevenir 
      # conflictos, en los métodos  públicos de escritura y lectura (SetData() 
      # y GetData()) :
      self._lock = threading.Lock()

      # Cuando se utiliza el simulador de Proteus es necesario limitar el 
      # volumen de datos a transmitir, se define el atributo throughput_limit
      # para definir si se limita o no el volumen de datos :
      self.throughput_limit = throughput_limit
      
      with self._lock :
         # Puerto serie utilizado para la comunicación :
         self.__comm = SerialDevice.Serial()

         try :

            # Se definen los parámetros de operación del puerto serie :
            self.__comm.port     = comm_name
            self.__comm.baudrate = 57600
            self.__comm.bytesize = 8
            self.__comm.parity   = 'N'
            self.__comm.timeout  = 0.5
            self.__xmitTimeout   = 0.5
            self.__comm.stopbits = 1
            self.__comm.xonxoff  = 0
            self.__comm.rtscts   = 0
            self.__comm.dsrdtr   = 0

            # Se abre el puerto serie :
            self.log.debug(u'Abriendo el puerto serie : %s', str(self.__comm))

            self.__comm.open()
            if comm_name == u'*OPPENING_IN_PROGRESS*' :
               comm_name = self.__comm.port
               # Ahor aa se puede identificar el manejador de reportes :
               self.log = report.report.getLogger(u'OTCProtocol.' + comm_name)
               
            self.log.debug(u'El puerto %s esta preparado para la comunicación.'\
                                                             % self.__comm.port)

         except SerialDevice.SerialException as e:
            raise OTCProtocolError(u'El puerto %s serie no existe o '
                                      u'no esta disponible' %comm_name, e, self)



