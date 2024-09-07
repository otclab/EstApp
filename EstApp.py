#!/usr/bin/python
# -*- coding: utf-8 -*-

# Compilador Programador de la Configuración de Usuario para EstCard

# TO DO : Completar la Ayuda de cada orden :

from cmds import *
from estCard import *
from common import *
general_help = u"""
  Aplicación para la configuración de las Tarjetas de control de Estabilizador EstCard.

  Uso :
    - Lectura o Modificación de la Escala de Medición :
          >  EstApp.py -s [? | Valor]

    - Lectura o Modificación de las Ganancias Fase-Neutro :
          >>  EstApp.py -g [?]
          >>  EstApp.py [-gR | -gS | -gT ] [? | Valor]

    - Calibración de las Ganancias Fase-Neutro :
          >> EstApp.py -cal | -calL | -calU |calV [conteo_inicial
                                                   [duración]] [[Siglent SDM3055 IP] -Y}

    - Lectura de las mediciones de Tensión  :
          >> EstApp.py -mon
          >> EstApp,py -mon cycle [filename]
          >> EstApp,py -mon sample [input|output] [log_file]

    - Modos de Operación :
          >> EstApp.py -m [?]
          >> EstApp.py -m nombre_atributo [ ? | valor_atributo ]

    - Lectura o Modificación de los Umbrales de los Taps :
          >> EstApp.py -u [?]
          >> EstApp.py -u total Nuevo_Valor_del_Numero_de_Cambios
          >> EstApp.py -u  Nro_de_Orden  Pos  Nuevo_Valor_del_Umbral

    - Lectura o Modificación de los tiempos de arranque y apagado :
          >> EstApp.py -t [?]
          >> EstApp.py -t [ off | corte | apagado | on | encendido ]
          >> EstApp.py -t tipo tiempo [por] [subtension | sobretension]
          >> EstApp.py -t tipo tiempo [por] tipo_evento Valor_del_Tiemo

    - Respaldo de la Configuración :
          >> EstApp.py -b [-mch | -intelhex | -source |
                                              -dump | -bin [<bacup_filename>]]
    - Operación Manual de los taps :
          >> EstApp.py -manual

    - Reordenamiento de la Activación de los Taps :
          >> EstApp.py -o [nuevo_orden]

    - Ayuda específica :
          >> EstApp.py -h [ -cmd]

      cmd puede ser cualquiera de las siguientes :
         -cal , -calibration, - calibración
         -s , scale, escala
         -b, -respaldo, -backup
         -g, -gain', -ganancia
         -m, -mode, -modo
         -manual, -settap
         -u, -umbral, -umbrales, -threshold, -thresholds
         -t, -timers, -tiempo, -tiempos, -temporizacion
         -mon, -monitor, '-monitoreo
         -o

  La tarjeta EstCard debe estar conectada al puerto serie de la computadora.

  Si la PC tiene un solo puerto serie, se utilizará este por defecto y no será
  necesario especificarlo. Por otro lado si el equipo tiene mas de un puerto
  serie, el programa interrogará al usuario para seleccionar uno de ellos,
  luego de listar y numerar los puertos serie disponibles.

  Opcionalmente el puerto serie a utilizar puede especificarse en la línea de
  ordenes según las siguientes reglas :

    (a) Especificar como la primera opción el puerto COM a utilizar precedida
        por el signo '-', por ejemplo para especificar puerto serie COM1 :

        >> EstApp.py -COM1 ...

    (b) Especificar la opción -port y a continuación especificar el nombre
        del puerto, por ejemplo para especificar el puerto CNA0

        >> EstApp.py  ...  -port CNA0 ...

        Esta opción es útil para nombres de puertos serie no estándares, como
        en el caso de algunos adaptadores USB o Bluetooth.

  Nótese que se utilizan los puntos suspensivos para indicar otras opciones de
  trabajo.

"""


def main(args):
    # Reconoce la especificación de la simulación del dispositivo por medio de
    # Proteus, lo retira de la lista de argumentos y prepara throughput_limit
    # para limitar el volumen de datos :
    if '-proteus' in args:
        i = args.index(u'-proteus')
        args.pop(i)
        throughput_limit = True
    else:
        throughput_limit = False

    # En Windows y Linux, la especificación del puerto es obligatoria para
    # ciertas opciones (y por lo tanto parsePort() debe interrogar al usuario :
    port, args = parsePort(args, ['-u', '-t', u'-g', u'-s'])

    # Inicializa el sistema de reporte :
    report('EstCard')
    logger = report.getLogger()

    if len(args) == 1:
        print('Use "EstApp.py -h|-help|help|ayuda|sos" para ayuda.\n')
        sys.exit(1)

    if args[1] in ['-h', '-help', 'help', 'ayuda', 'sos']:
        if len(args) == 2:
            # print version.version_doc
            print(general_help)
            sys.exit(0)

        topic = args[2]
        if (len(topic) == 2) and (topic[0] == '-'):
            topic = topic[1:]

        if topic in ['cal', 'calibration', 'calibracion']:
            print((CalCmd.__doc__))
            sys.exit(0)

        if topic in ['b', 'respaldo', 'backup']:
            print((BackupCmd.__doc__))
            sys.exit(0)

        if topic in ['g', 'gain', 'ganancia']:
            print((GainCmd.__doc__))
            sys.exit(0)

        if topic in ['m', 'mode', 'modo']:
            print((ModeCmd.__doc__))
            sys.exit(0)

        if topic in ['s', 'scale', 'escala']:
            print((ScaleCmd.__doc__))
            sys.exit(0)

        if topic in ['manual', 'settap']:
            print((SetTapCmd.__doc__))
            sys.exit(0)

        if topic in ['u', 'umbral', 'umbrales', 'threshold', 'thresholds']:
            print((ThresholdCmd.__doc__))
            sys.exit(0)

        if topic in ['t', 'timers', 'tiempo', 'tiempos', 'temporizacion']:
            print((TimersCmd.__doc__))
            sys.exit(0)

        if topic in ['mon', 'monitor', 'monitoreo']:
            print((MonCmd.__doc__))
            sys, exit(0)

        if topic in ['o', 'orden']:
            print((OrderingTapCmd.__doc__))
            sys, exit(0)

        print('Error : No existe el tema de ayuda.')
        sys.exit(1)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Lectura de la EEPROM y generación de su respaldo :
    elif args[1] == '-b':
        BackupCmd(args, port, throughput_limit)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # TODO : Medición de la Relación de Taps :
    elif args[1] in [u'-taprel']:
        card = openCard(port, throughput_limit)
        card.EnterRemoteMode()

        for tap in range(1, card.get('Taps Utilizados') + 1):
            # Se activa el tap a medir :
            card.set('Tap Activo', tap)
            print('Tap : %d' % tap)

            # La medición de la entrada y salida :
            try:
                MeasureTask(card)
            except Exception as e:
                print('Error - La medición aborto')
                sys.exit(1)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Operación Manual de los Taps:
    elif args[1] in [u'-manual']:
        SetTapCmd(port, throughput_limit)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Calibración:
    elif args[1] in [u'-cal', u'-calL', u'-calU', u'-calV']:
        CalCmd(args, port, throughput_limit)

    elif args[1] in [u'-g', u'-gL', u'-gU', u'-gV']:
        GainCmd(args, port, throughput_limit)

    elif args[1] == u'-m':
        ModeCmd(args, port, throughput_limit)

    elif args[1] == '-t':
        TimersCmd(args, port, throughput_limit)

    elif args[1] == '-s':
        ScaleCmd(args, port, throughput_limit)

    elif args[1] == '-u':
        ThresholdCmd(args, port, throughput_limit)

    elif args[1] == u'-mon':
        card = MonCmd(args, port, throughput_limit)

    elif args[1] == '-test':
        TestCmd(args, port, throughput_limit)

    elif args[1] == '-o':
        OrderingTapCmd(args, port, throughput_limit)

    else:
        print("'{:s}' orden desconocida.".format(args[1]))


if __name__ == '__main__':
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
    try:
        main(sys.argv)
    except OTCProtocolError as e:
        pass

    finally:
        # if card is not None : card.close()
        pass
