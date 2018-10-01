    #!/usr/bin/python
# -*- coding: utf-8 -*-

# Compilador Programador de la Configuración de Usuario para EstCard

# TO DO : Completar la Ayuda de cada orden :

general_help = u"""
  Aplicación para la configuración de las Tarjetas de control de Estabilizador EstCard.

  Uso :
    -Calibración :
     >> EstApp.py -cal | -calL | -calU |calV [conteo_inicial [duración]]

    - Lectura o Modificación de las Ganancias Fase-Neutro :
              MVParser.py -g [? | Valor_R Valor_S Valor_T]
              MVParser.py [-gR | -gS | -gT ] [? | Valor]

    - Lectura o Modificación de la Escala de Medición :
              MVParser.py -s [? | Valor]

    - Calibración de las Ganancias Fase-Neutro :
              MVParser.py [ -cal | -calR | -calS | -calT ]

    - Compilación del programa usuario :
              MVParser.py -c FileName [-user_program | -source |
                                            -dump | -mch | -intelhex |
                                            -bin  Bin_FileName ]

    - Compilación y Programación del programa usuario :
              MVParser.py -p FileName [-user_program | -source |
                                            -dump | -mch | -intelhex |
                                            -bin  Bin_FileName ]

    - Respaldo de la Configuración :
         >> EstApp.py -b [-mch | -intelhex | -source |
                                              -dump | -bin <bacup_filename>]

    - Operación Manual de los taps :
         >> EstApp.py -manual

    - Ayuda específica :
              MVParser.py -h [ -b | -g | -s | -cal | -c | -p | -lang | -format]

  Excepto para la operación de compilación, la tarjeta MVoltLCD debe estar
  conectada al puerto serie de la computadora.

  Si la PC tiene un solo puerto serie, se utilizará este por defecto y no será
  necesario especificarlo. Por otro lado si el equipo tiene mas de un puerto
  serie, el programa interrogará al usuario para seleccionar uno de ellos,
  luego de listar y numerar los puertos serie disponibles.

  Opcionalmente el puerto serie a utilizar puede especificarse en la línea de
  ordenes según las siguientes reglas :

    (a) Especificar como la primera opción el puerto COM a utilizar precedida
        por el signo '-', por ejemplo para especificar puerto serie COM1 :

        >> MVParser.py -COM1 ...

    (b) Especificar la opción -port y a continuación especificar el nombre
        del puerto, por ejemplo para especificar el puerto CNA0

        >> MVParser.py  ...  -port CNA0 ...

        Esta opción es útil para nombres de puertos serie no estándares, como
        en el caso de algunos adaptadores USB o Bluetooth.

  Nótese que se utilizan los puntos suspensivos para indicar otras opciones de
  trabajo.

"""



import sys
import math
from time import sleep
import struct

import common.report

from otcCard.OTCProtocol import *
from otcCard.OTCCard import *
from estCard.EstCard import *
from cmds import *
from common import *
# import version

#card = None



# Función auxiliar reconoce la opción op (-g, -cal) de trabajo simultáneo en
# todas las fases o lsa especificas por fase donde op es el prefijo. precedido
# por el nombre de la fase (R, S o T).
def parsePhases(arg, op, card = None) :
   class _phase(object) :
      """
      Clase de Intermediación 'por referencia' (Proxy Class) de los atributos
      (de la clase EstCard.Phase, i.e. L, U, V) de su atributo propio 'card'
      Tiene otro atributo propio denominado 'label' que contiene el nombre
      público (i.e. R, S o T) de la fase de interés.
      """

      # Diccionario de la correspondencia entre los nombres públicos e internos
      # de cada fase :
      internal_name = {'L' : 'LN', 'U' : 'UV', 'V' : 'UV'}

      def __init__(self, label) :
         self.label = label
         self.card = card

      def __getattr__(self, name) :
         phase = self.card.__getattribute__(_phase.internal_name[self.label])
         return phase.__getattribute__(name)

      def __setattr__(self, name, value) :
         if name in ['label', 'card'] :
            self.__dict__[name] = value
         else :
            phase = self.card.__getattribute__(_phase.internal_name[self.label])
            setattr(phase, name, value)

      def __str__(self) :
         phase = self.card.__getattribute__(_phase.internal_name[self.label])
         return phase.__str__()


   if arg[1] == op :
     return [_phase('L'), _phase('U'), _phase('V')]

   elif arg[1] == (op + 'L') :
     return [_phase('R')]

   elif arg[1] == (op + 'V') :
     return [_phase('S')]

   elif arg[1] == (op + 'T') :
     return [_phase('T')]




def main(args) :
  global card

  # En Android, Python no reconoce la codificación del terminal y es necesario
  # asignarlo, se utiliza 'utf-8' por ser el mas compatible :
  import locale

  import codecs
  codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

  if (sys.stdout.encoding is None) and (locale.getpreferredencoding() is None) :
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

  # Los argumentos de la línea de ordenes, por defecto están codificados de
  # acuerdo a la de la consola y deben re-codificarse al estándar utilizado
  # en el programa (unicode):
  for i, arg in enumerate(args) :
    args[i] = arg.decode(locale.getpreferredencoding())

  # Reconoce la especificación de la simulación del dispositivo por medio de
  # Proteus, lo retira de la lista de argumentos y prepara throughput_limit
  # para limitar el volumen de datos :
  if '-proteus' in args :
    i = args.index(u'-proteus')
    args.pop(i)
    throughput_limit = True
  else :
    throughput_limit = False

  # Reconoce la especificación del puerto de comunicaciones y lo retira del
  # vector de argumentos :
  if '-android' in args :
    # En Android la especificación del puerto es solicitada al usuario al
    # abrir el puerto (por la fachada bluetooth), si existe en la línea de
    # ordenes se ignora :
      i = args.index(u'-android')
      args.pop(i)
      # pero de todas maneras debe retirarse :
      port, args = parsePort(args)
  else :
    # En Windows y Linux, la especificación del puerto es obligatoria para
    # ciertas opciones (y por lo tanto parsePort() debe interrogar al usuario :
    port, args = parsePort(args, ['-u', '-t', u'-g', u'-s'])

  # Inicializa el sistema de reporte :
  report('EstCard')
  logger = report.getLogger()

  if len(args) == 1 :
    print u'Use "EstApp.py -h|-help|help|ayuda|sos" para ayuda.\n'
    sys.exit(1)

  if args[1] in ['-h', '-help', 'help', 'ayuda', 'sos'] :
    if len(args) == 2 :
      #print version.version_doc
      print general_help
      sys.exit(0)

    topic = args[2]
    if (len(topic) == 2) and (topic[0] == '-') : topic = topic[1:]


    if topic in ['-cal', 'calibration', 'calibracion'] :
      print CalCmd.__doc__
      sys.exit(0)



    if topic in ['b', 'respaldo', 'backup'] :
      print BackupCmd.__doc__
      sys.exit(0)

    if topic in ['g', 'gain', 'ganancia'] :
      print GainCmd.__doc__
      sys.exit(0)

    if topic in ['m', 'mode', 'modo'] :
      print ModeCmd.__doc__
      sys.exit(0)

    if topic in ['s', 'scale', 'escala'] :
      print scaleCmd.__doc__
      sys.exit(0)

    if topic in ['-manual', 'manual', 'settap'] :
      print SetTapCmd.__doc__
      sys.exit(0)

    if topic in ['u', 'umbral', 'umbrales', 'threshold', 'thresholds'] :
      print ThresholdCmd.__doc__
      sys.exit(0)

    if topic in ['t', 'timers', 'tiempo', 'tiempos', 'temporizacion'] :
      print TimersCmd.__doc__
      sys.exit(0)

    if topic in ['mon', 'monitor', 'monitoreo'] :
      print MonCmd.__doc__
      sys,exit(0)

    print u'Error : No existe el tema de ayuda.'
    sys.exit(1)

  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  # Lectura de la EEPROM y generación de su respaldo :
  elif args[1] == '-b' :
    BackupCmd(args, port, throughput_limit)

  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  # TODO : Medición de la Relación de Taps :
  elif args[1] in [u'-taprel'] :
    card = openCard(port, throughput_limit)
    card.EnterRemoteMode()

    for tap in range(1, card.get('Taps Utilizados') + 1) :
      # Se activa el tap a medir :
      card.set('Tap Activo', tap)
      print u'Tap : %d' %tap

      # La medición de la entrada y salida :
      try :
        MeasureTask(card)
      except Exception as e :
        print 'Error - La medición aborto'
        sys.exit(1)


  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  # Operación Manual de los Taps:
  elif args[1] in [u'-manual'] :
    SetTapCmd(port, throughput_limit)

  # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  # Calibración:
  elif args[1] in [u'-cal', u'-calL', u'-calU', u'-calV'] :
    CalCmd(args, port, throughput_limit)

  elif args[1] in [u'-g', u'-gL', u'-gU', u'-gV'] :
    GainCmd(args, port, throughput_limit)

  elif args[1] == u'-m' :
    ModeCmd(args, port, throughput_limit)

  elif args[1] == '-t' :
    TimersCmd(args, port, throughput_limit)

  elif args[1] == '-s' :
    scaleCmd(args, port, throughput_limit)

  elif args[1] == '-u' :
    ThresholdCmd(args, port, throughput_limit)

  elif args[1] == u'-mon' :
    card = MonCmd(args, port, throughput_limit)

  elif args[1] == '-test' :
    TestCmd(args, port, throughput_limit)

  elif args[1] == '-o' :
    OrderingTapCmd(args, port, throughput_limit)

if __name__ == '__main__' :
  # Las excepciones causadas por errores de comunicación (OTCProtocolError) se
  # se reportan en la consola directamente por el sistema de reporte (logger),
  # por lo que se atrapan para impedir el reporte estándar de python.
  #
  # En general las excepciones restantes (previstas por un mal formato de
  # entrada) son atrapadas en main e inician el procedimiento de limpieza, para
  # finalmente reportar su ocurrencia con un mensaje apropiado al contexto,,
  # evitando mostrar el mensaje de diagnostico estándar de Python.
  #
  # Los errores causados por un defecto en el programa, no son atrapadas y
  # producen el mensaje de diagnóstico estándar.
  try :
    main(sys.argv)
  except OTCProtocolError as e :
    pass

  finally :
    #if card is not None : card.close()
    pass