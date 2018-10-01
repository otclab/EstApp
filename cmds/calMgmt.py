#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *

def GetCountLength(args) :
    # Se obtienen los tiempos de las cuentas regresivas de inicio y muestreo :
    try :
       start_count_down  = int(args[2]) if (len(args) > 2) else 5
    except :
       start_count_down = -1

    if start_count_down < 0 :
       print u'"%s" no es un número entero no negativo.'% args[2]
       sys.exit(1)

    try :
       length_count_down  = int(args[3]) if (len(args) > 3) else 5
    except :
       length_count_down = -1

    if start_count_down < 0 :
       print u'"%s" no es un número entero no negativo.' % args[3]
       sys.exit(1)

    return (start_count_down, length_count_down)


def Measuring(card, phase, start_count_down = 0, length_count_down = 10) :
  try :
    from winsound import Beep
  except :
    def Beep(tone, time) :
      print '\a'

  # Cuenta regresiva para el inicio de la medición :
  for i in range(0, start_count_down) :
    print u'Inicio en : %2d\x0D' %(start_count_down - i) ,
    Beep(2500, 120)
    sleep(0.880)
  Beep(3600, 1000)

  # Se inicia la medición, se asegura de preparar el dispositivo para que
  # se realice en el modo Fase-Neutro (TODO No esta implementado en el uC,
  # por eso se solicita al usuario que ajuste las conexiones para iniciar
  # la calibración) :
  try :
    #card.EnterRemoteMode()
    card.StartMeasure(phase + ' Cal')

  except Exception as e :
     card.close()
     if type(e) != OTCProtocolError : print e
     sys.exit(1)

  # Medición, cuenta regresiva y presentación de su progreso :
  for i in range(0, length_count_down) :
    if not card.measure.is_alive() : break

    print u'Final en %d :  ' % (length_count_down - i),
    print u'[L-N] %s, ' % card.LN,
    if (phase == 'L') or (type(card) == EstCard1V0) :
      print u'[U-V] %s, ' % card.UV
    else :
      print u'[%s-N] %s, ' % (phase, card.UV)

    if (i == (length_count_down - 1)) :
        Beep(2500, 1000)

    else :
        Beep(2500, 120)
        sleep(0.880)

  card.StopMeasure()
  # TODO Verificar si es necesario -> card.close()

  # Presentación de los resultados :
  print u'\nResumen de la medición :\n    ',
  print u'[L-N] %s, ' % card.LN,
  if (phase == 'L') or (type(card) == EstCard1V0) :
    print u'[U-V] %s, ' % card.UV
  else :
    print u'[%s-N] %s, ' % (phase, card.UV)



def CalCmd(args, port, throughput_limit) :
  u"""
  EstParser : Calibración
  =======================

  Uso :
     >> EstParser.py -cal | -calL | -calU |calV [conteo_inicial [duración]]

  El principio de la calibración consiste en medir el promedio de la tensión
  tanto por la tarjeta EstCard, como en un instrumento de referencia, para
  a continuación calcular los valores de ganancia de cada fase para igualarla
  a la del instrumento de referencia.

  El procedimiento de calibración, se inicia con una cuenta regresiva, al
  final de la cual se inicia el cálculo del promedio de la tensión por la
  tarjeta EstCard, simultáneamente debe iniciarse el registro de esta
  por el instrumento de referencia.

  El intervalo de tiempo durante el cual se realiza el cálculo del promedio
  de la tensión, se señala por una segunda cuenta regresiva, al final de la
  cual termina el cálculo del promedio de la tensión y deberá detenerse el
  registro en el instrumento de referencia.

  En una tercera etapa, el programa interroga al usuario por la medición del
  valor promedio de la tensión, cuando se ingrese el valor, se calcularán las
  ganancias respectivas y se interroga al usuario por su aprobación para
  proseguir con su modificación.

  Como instrumento de referencia, se pueden utilizar diversas series de
  multímetros Fluke con capacidad de registro (tecla [MAX MIN]), el inicio
  del registro se realiza pulsando la tecla [MAX MIN], para detener
  (congelar) el registro se pulsa la tecla [HOLD], el valor del promedio
  se puede obtener pulsando la tecla [MAX MIN] hasta que aparezca la leyenda
  AVG en la pantalla.

  La calibración se puede realizar independientemente en cada fase (opciones
  -calR, -calS, calT), o simultáneamente en las tres fases (opción -cal), no
  obstante en este caso deberá medirse la misma tensión en las tres fases, lo
  que implica que deben estar conectadas entre sí. En cualquier caso, la
  tensión de calibración siempre es la tensión Fase-Neutro.

  Los tiempos de las cuentas regresivas se pueden definir por medio de dos
  números opcionales seguidos de la opción (-cal, -calR,...,etc.), el
  primero (conteo_inicial) de los cuales es el tiempo (en segundos) de la
  cuenta regresiva para iniciar la medición y el segundo el de la cuenta
  regresiva de la duración del muestreo.
"""

  try :
    from winsound import Beep
  except :
    def Beep(tone, time) :
      print '\a'

  start_count_down, length_count_down = GetCountLength(args)

  # Se inicia la comunicación con el dispositivo :
  card = openCard(port, throughput_limit)

  # Detrmina la fase de trabajo :
  phase = args[1][-1] if len(args[1]) > 4 else 'L'

  # Comprueba si la fase de trabajo existe en la tarjeta :
  if not phase in card.inputs_available() :
    print 'La entrada %s no existe en la tarjeta de modelo %s' %(phase,
                                                   card.id['hardware_model'])
    sys.exit(-1)

  # Se advierte al usuario de las conexiones necesarias :
  print  u'Calibración de la Fase %s-N (Entrada %s)\n' %(phase, phase)
  if (type(card) == EstCard1V0) or (phase == 'L') :
    print u'Las entradas L y N deben estar alimentadas con la tensión ' \
          u'nominal \ny simultánemente debe prepararse para medirse con ' \
          u'el multímetro.\n'
    if phase != 'L' :
      print u'Además la entrada %s debe conectarse con la entrada L' %phase
      print u'y la entrada %s con la entrada N.\n' %('V' if phase == 'S'
                                                                    else 'S')

  else :
    print u'Las entradas L y %s deben estar conectadas entre si, deben\n' \
          u'alimentarse con respecto a la entrada N con la tensión nominal\n'\
          u'y simultánemente debe prepararse para medirse.\n' % (phase)

  # Realiza la medición y su presentación :
  Measuring(card, phase, start_count_down, length_count_down)

  # Se interroga por el valor de la medición de referencia, solo cuando se
  # calibra la fase L(-N)  :
  if phase == 'L' :
    while True :
       try :
         ans = raw_input('\n\nValor de Referencia : ').decode(sys.stdin.encoding)

         if ans == 'x' :
           print u'\nNo se programo el valor a elección del usuario.'
           sys.exit(0)

         Vref = float(ans)
         break

       except ValueError as e :
         print u"Error - Valor numérico inválido, 'x' para "                 \
                                                  u"abandonar la calibración."

       except Exception as e :
        print repr(e)
  else :
    Vref = card.LN.rms

  # Se invoca al calibrador de la fase, de manera de acceder a la ganancia
  # actual y la nueva, de sus representaciones interna y la medición justo
  #realizada :
  try :
    cal = card.calibrator(phase, Vref)

  except ValueError as e :
    print u'Error - No se puede continuar con la calibración.'
    print u'%s' %e.message
    card.close()
    sys.exit(1)

  # Se porponen los cambios ...
  try :
    print u'\nEl valor actual %s del factor de calibración de la fase %s, ' \
          u'\nse remplazará por (%s) \n' %(cal.old, phase, cal.new)

    while True :
      ans = raw_input('Se acepta ?  [S/N]').decode(sys.stdin.encoding)
      if ans.lower() in ['s', 'si', 'n', 'no'] : break

    # y se solicita la autorización para el cambio :
    if ans.lower() in ['s', 'si'] :
      cal.commit()
      print u'\nLa ganancia se reajusto.\n'
    else :
      print u'\nNo se programo el valor a elección del usuario.\n'

    card.ExitRemoteMode()

  except OTCProtocolError :
    # En este punto el 'logger' reporto la descripción del error en la
    # consola y no hay nada que hacer.
    pass

  card.close()

  sys.exit(0)



