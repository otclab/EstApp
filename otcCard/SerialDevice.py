#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO El módulo RN42 no acepta el cambio de parámetros de comunicación
# TODO por medio del perfil SPP, por lo tanto también debe ejecutarse
# TODO su ajuste.
"""
SerialDevice.py

Encapsula las propiedades mínimas del puerto serie necesarias para OTCProtocol,
a saber : __init__(), open(), write(), read(), flushInput() y close()

La API provista es similar a la del módulo PySerial, de hecho para los sistemas
operativos estándar, las clases serial_device.Serial y serial_device.SerialExce-
ption se heredan directamente de las clases serial.Serial y serial.SerialExcep-
tion, sin ninguna modificación.

En general los módulos adaptadores seriales Bluetooth, deben instalarse previa-
mente en el sistema operativo, después de lo cual su enumeración como un puerto
serie del sistema y la asignación de su nombre o identificador se realiza
automáticamente, quedando apto para manejarse en forma estándar.

A despecho de ser una distribución Linux, Android en general no permite la
instalación, sin embargo permite las operaciones básicas de comunicación con
el módulo por medio de la fachada Bluetooth.

Si el módulo soporta el perfil SPP, la configuración de los parámetros de comu-
nicación del puerto físico, deberían ser definidas por medio de la API estándar
del puerto serie.

En Android sin embargo no existe tal API, ni la fachada Bluetooth provee acceso
al canal de control RFCOM del dispositivo, por lo que la configuración debe
llevarse a cabo por medio de los ordenes AT del módulo, las cuales no son
estándar y dependen del modelo/marca del dispositivo.

Por el momento solo los dispositivos basados en el radio bñuetooth RN42 son
soportados.

La API se extiende con la función com_list(), que devuelve un vector cuyos
elementos son los nombres de los dispositivos registrados como puerto serie,
para Android devuelve el vector [None], de manera no devolver un vector vacío
e informar que no existen puertos registrados, pero dejando la posibilidad
que se seleccione al intentar conectarse, por medio del menú desplegado por
defecto, en el dispositivo Android.

"""

from common.report import report
from .OTCProtocolError import OTCProtocolError

# Android se reconoce por la existencia del módulo 'android' :
try :
  import android
  isAndroid = True
except ImportError :
  isAndroid = False

if not isAndroid :
  # Se trata de un sistema operativo estándar, el soporte del puerto serie es
  # provisto por el módulo PySerial :
  import serial
  import serial.tools.list_ports

  class SerialDevice(serial.Serial) :

    def __init__(self, *args, **kwargs):
      self.log = report.getLogger(u'SerialDevice')
      super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs) :
      try :
        super().open(*args, **kwargs)

      except (serial.SerialException, serial.SerialTimeoutException) as e :
        raise OTCProtocolError('El puerto %s serie no existe o '
                               'no esta disponible.' % self.port, e, self)

    def write(self, *args, **kwargs) :
      try :
        super().write(*args, **kwargs)

      except (serial.SerialException, serial.SerialTimeoutException) as e :
        raise OTCProtocolError('El puerto %s no responde.' % self.port, e, self)


  def com_list() :
    u"""
    Devuelve una lista con los (nombres de los) puertos serie disponibles en
    el sistema.
    """
    #[TO DO] : Eliminar de la lista los puertos no disponibles.
    #          La lista de puertos es realmente la de los existentes, incluyendo
    #          aquellos que no están disponibles, i.e que están siendo utilizados
    #          por otra aplicación.
    import os
    import _winreg
 
    port_list = []
 
    # Existe un defecto en la función 'list_ports.comports' por la cual no
    # lista los puertos USB en Windows8 (y posiblemente 7) del módulo serial.
    # tools, como solución se obtiene la lista de puertos del registro de
    # windows directamente.
    if os.name == 'nt' :
       path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
 
       try:
          key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)
          i = 0
          port_list = {}
          while 1 :
             val = _winreg.EnumValue(key, i)
             port_list[str(val[0])] = str(val[1])
             i = i+1
 
       except WindowsError:
          pass
 
    else :
       com_ports = serial.tools.list_ports.comports()
       for i in com_ports :
          port_list += [i[0]]
 
    return port_list

else :
  import RN42Serial

  class SerialException(IOError):
    """Base class for serial port related exceptions."""
    pass

  class Serial(RN42Serial.RN42Serial) :
    pass
    
    @staticmethod
    def exception(msg) :
      return SerialException(msg)


  def com_list() :
   # Se supone que el dispositivo Android no tiene puertos serie nativos,
   # se devuelve un vector con un elemento None, de manera de forzar el
   # despliegue del navegador de dispositivos Bluettooth para la selección
   # por parte del usuario del dispositivo :
   return [None]










