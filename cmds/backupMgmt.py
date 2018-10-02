#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from cmds import intelhex
from common import openCard


# Dirección de Inicip del Volcado de la EEPROM :
EEPROM_START = 0x00


def get_dump(data) :
  """
  Devuelve la representación tabular del contenido de data.
  """
  str = u''
  for n in range(0, len(data), 8) :
    str += u'0x%02X : ' % (n + EEPROM_START)
    bytes_of_line = [data[i] for i in range(n, n+8) if i < len(data)]
    str += u" ".join(['0x{0:02X}'.format(b) for b in bytes_of_line])
    str += u" "*(46 - len(str)%59)
    str += u"  | " + "".join(chr(b) if (b > 31) and (b < 128) else u'.' for b in
                             bytes_of_line)
    str += u'\n'

  return str


def get_intelhex(data) :
  """
  Genera la representación en el formato IEEE754 del contenido de la EEPROM
  según el formato de Microchip.
  """

  # Al contrario con la asignación natural (utilizada por el microcontrolador),
  # i.e. asigna la dirección en forma secuencial, iniciándola desde 0, a cada
  # byte de la EEPROM, Microchip considera que cada posición de la EEPROM como
  # de 16 bits, considerando el byte MSB igual a cero, y reasigna la dirección
  # de cada posición considerándola como de dos bytes, donde el byte LSB
  # anteceda al byte (virtual) MSB, nuevamente iniciando desde 0 y hasta 2*N-1
  # donde N es el número de bytes de la EEPROM.

  data_16bit = [data[n // 2] if n % 2 == 0 else 0 for n in range(2 * len(data))]

  # En el formato IntelHex, Microchip asigna a la EEPROM en un segmento de
  # direcciones lineal y con la dirección EEPROM_ADDRESS.
  EEPROM_ADDRESS = 0x0001E000

  # Se inicia los registros IntelHex, definiendo la dirección base del segmento
  # de direcciones lineal :
  records = [intelhex.UlbaRecord(EEPROM_ADDRESS//65536)]

  # Se continua definiendo los registros Intelhex con el contenido de la EEPROM
  # cada 16 bytes :
  BYTES_PER_RECORD = 16
  for n in range(0, len(data_16bit), BYTES_PER_RECORD) :
    records += [intelhex.DataRecord(
               (EEPROM_ADDRESS % 65536) + (2*n + EEPROM_START),
               [data_16bit[i] for i in range(n, n+BYTES_PER_RECORD)
                                                      if i < len(data_16bit)])]

  # Finalmente el registro de fin :
  records += [intelhex.EndRecord()]

  # Se crea la representación paramétrica del conjunto de registros ...
  hex = intelhex.IntelHex(records)

  # y se devuelve su representación textual :
  return hex.__str__()


def get_source(data) :
  u"""
  Genera texto compatible con el compilador C XC8, para definir el contenido
  de la EEPROM, mediante la macro instrucción __EEPROM_DATA. (Obsoleta)
  """
  # La macro función __EPROM_DATA necesita un argumento de 8 bytes, se completa
  # el programa añadiendo bytes de valor 0x00, a fin de completar su longitud
  # de manera que sea un múltiplo de 8 :
  if (len(data) % 8) > 0 :
    data += [0x00]*(8 - len(data) % 8)

  str = u''
  for n in range(0, len(data), 8) :
    str += u'__EEPROM_DATA('
    bytes_of_line = [data[i] for i in range(n, n+8) if i < len(data)]
    str += u", ".join([u'0x{0:02X}'.format(b) for b in bytes_of_line])
    str += u') ;\n'

  return str


def BackupData2str(data, format = None, backup_filename = None) :
  if format is None :
    # Por defecto se presenta el contenido hexadecimal :
    txt = get_dump(data)

  elif format == '-mch' :
    txt = '%s\n' % "\n".join(['0x{0:02X}'.format(b) for b in data])

  elif format == '-intelhex' :
    txt = get_intelhex(data)

  elif format == '-source' :
    txt = get_source(data)

  elif format == '-dump' :
    txt = get_dump(data)

  elif format == '-bin' :
    txt = get_dump(data)

  else :
    raise AttributeError(u"Error : Formato '%s' desconocido." % format )

  try :
    if backup_filename is not None :
      with open(backup_filename, 'wb') as file :
        if (format == '-bin') :
          file.write(str(bytearray(data)))
        else :
          file.write(txt.encode('utf-8'))

      print('Se genero el archivo : %s\n' % backup_filename)
    else :
      print('Advertencia : No se específico el archivo de salida.\n')

  except IOError as e :
    if e.errno == errno.ENOENT :
      sp = 'Error : No existe el directorio.'

    elif e.errno == errno.EBADF :
      sp = 'Error : Número de archivo incorrecto.'

    elif e.errno == errno.EEXIST :
      sp = 'Error : El archivo ya existe.'

    elif e.errno == errno.EMFILE :
      sp = 'Error : Demasiados archivos abiertos.'

    elif e.errno == errno.EFBIG :
      sp = 'Error : Archivo demasiado grande.'

    elif e.errno == errno.EROFS :
      sp = u'Error : Sistema de archivos de solo lectura. '

    elif e.errno == errno.EACCES :
      sp = u'Error : Permiso de escritura rechazado.'

    else :
      print('Error : %s.' % e.args[1])

    raise IOError(e.errno, sp)

  return txt

def BackupCmd(args, port, throughput_limit) :
  """
  EstApp : Resguardo de la configuración
  ======================================

  El uso en general es :
     >> EstApp.py -b [-opcion_de_formato [opcion_Archivo_de_Respaldo]]

  en particular  :
     >> EstApp.py -b [-mch | -intelhex | -source | -dump [<backup_filename>] ]
     >> EstApp.py -b -bin <backup_filename>]

  Lee toda la configuración y la presenta o almacena (opcionalmente) en un archivo.
  (Es decir todo el contenido de la EEPROM del microcontrolador).

  Las opciones de formato son :

     Tabular (opción -dump)
        Presentación de forma simple del contenido, de 16 bytes por linea
        separados por espacios, con una primera columna con la dirección
        inicial de los bytes de la misma.

     Microchip .mch (opción -mch)
        Presentación del contenido en forma ordenada un byte por linea.

     IntelHex (opción -intelhex)
        Presentación del contenido en el formato IntelHex.

     C (opción -source)
        Genera texto compatible con el compilador C XC8, para definir el
        contenido de la EEPROM (i.e. la serie de instrucciones EEPROM_DATA
        que define el contenido respectivo).

     Binario (opción -bin)
        Genera un archivo binario (con el nombre del argumento adicional),
        con el contenido.

  El nombre del archivo de resguardo es opcional, en todos los casos excepto
  en el formato binario para la cual es obligatoria.

  Ejemplos :
      - Respaldo de la configuración y presentación solo en la consola,
        en el formato simple :
          >> EstApp.py  -b  -dump

      - Respaldo de la configuración en el archivo 'respaldo.txt' en el
        formato INTELHEX :
          >> EstApp.py  -b  -intelhex  respaldo.txt

"""
  card = openCard(port, throughput_limit)

  if len(args) > 4 :
    print('Advertencia : Demasiados argumentos.\n')

  arg = [card.eeprom]
  arg.extend(args[2:4])

  try :
    backup_txt = BackupData2str(*arg)
  except AttributeError as e :
    print(e.message)
    sys.exit(1)
  except IOError as e :
    print(e.args[1])
    sys.exit(1)

  # Se presenta en la consola el contenido del archivo :
  print("Configuración Completa : \n")
  print(backup_txt)

  card.close()



