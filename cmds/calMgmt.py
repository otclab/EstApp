#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *
import winsound

def short_beep():
  # Tono de 2500Hz generado durante 120 mS.
  winsound.PlaySound('beeps\short_beep.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)


def long_beep():
  # Tono de 2500Hz generado durante 1000 mS.
  winsound.PlaySound('beeps\long_beep.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)


def count_beep(count, total_count) :
  stat = (count == (total_count - 1))
  if stat :
    long_beep()
  else :
    short_beep()

  sleep(1.000)
  return stat


def is_IP(str_ip) :
  fields = str_ip .split('.')
  return  (len(fields) == 4) and (all([x.isdigit() and (int(x) < 256) for x in fields]))


def GetCountLength(args) :
    # Se obtienen los tiempos de las cuentas regresivas de inicio y muestreo :
    try :
       start_count_down  = int(args[2]) if (len(args) > 2) else 5
    except :
       start_count_down = -1

    if start_count_down < 0 :
       print('"%s" no es un número entero no negativo.'% args[2])
       sys.exit(1)

    try :
       length_count_down  = int(args[3]) if (len(args) > 3) else 5
    except :
       length_count_down = -1

    if start_count_down < 0 :
       print('"%s" no es un número entero no negativo.' % args[3])
       sys.exit(1)

    return (start_count_down, length_count_down)


def Measuring(card, phase, start_count_down = 0, length_count_down = 10, ref_measure = None) :

  # Cuenta regresiva para el inicio de la medición :
  for i in range(0, start_count_down) :
    print('Inicio en : %2d' %(start_count_down - i), end = '\r')
    count_beep(i, start_count_down)

  # Se inicia la medición, se asegura de preparar el dispositivo para que
  # se realice en el modo Fase-Neutro (TODO No esta implementado en el uC,
  # por eso se solicita al usuario que ajuste las conexiones para iniciar
  # la calibración) :
  try :
    #card.EnterRemoteMode()
    card.StartMeasure()
    if ref_measure : ref_measure.start_measure()

  except Exception as e :
     card.close()
     if type(e) != OTCProtocolError : print(e)
     sys.exit(1)

  # Medición, cuenta regresiva y presentación de su progreso :
  for i in range(0, length_count_down) :
    if not card.measure.is_alive() : break

    print('\rFinal en %3d :  ' % (length_count_down - i),
          '[L-N] %s, ' % card.LN, end = '')
    if (phase == 'L') or (type(card) == EstCard1V0) :
      print('[U-V] %s, ' % card.UV, end = '')
    else :
      print('[%s-N] %s, ' % (phase, card.UV), end = '')

    if ref_measure is not None:
      print(' [REF] %7.2f' %ref_measure.avg, end = '')

    print('\r', end = '')

    if count_beep(i, length_count_down) :
      card.StopMeasure()
      if ref_measure: ref_measure.stop_measure()


  # TODO Verificar si es necesario -> card.close()

  # Presentación de los resultados :
  print('\nResumen de la medición :\n    ', end=' ')
  print('[L-N] %s, ' % card.LN, end=' ')
  if (phase == 'L') or (type(card) == EstCard1V0) :
    print('[U-V] %s, ' % card.UV, end=' ')
  else :
    print('[%s-N] %s, ' % (phase, card.UV), end=' ')

  print(' [REF] %7.2f' %ref_measure.avg)

def CalCmd(args, port, throughput_limit) :
  """
  EstApp : Calibración
  =======================

  Uso :
     >> EstApp.py -cal | -calL | -calU |calV [conteo_inicial [duración]] [[Siglent SDM3055 IP] -Y}

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

    Se puede utilizar un instrumento de referencia conectado a la red, su IP
    debe ir como parámetro final y solo se aceptan direcciones IP numéricas.
    A la fecha solo el multimetro SDM3055 es soportado.

    En el caso de utilizarse un instrumento de referecnia se puede utilizar la
    opción -Y, para saltarse la autorización de la calibración.
  """

  # Reconoce si el último parámetro es una dirección IP :
  skip = args[-1] in ['-Y', '-y']
  if skip :  args.pop(-1)

  if is_IP(args[-1])  :
    # Reconoce el instrumento de referencia :
    from . import SDM3055
    ip = None
    try :
      ip = args.pop(-1)
      dmm = SDM3055.SDM3055(ip)
      ref_measure = SDM3055.VACMeasure(dmm)
      print('Calibrador Modelo %s, %s, Nº %s\n' %(dmm.model, dmm.manufacturer, dmm.num_serie))
    except Exception as e:
      print("Error al comunicarse con el instrumento de referencia (%s)" %ip)
      print('(%s)' %e.message)
      sys.exit(-1)
  else :
    ref_measure = None

  # Reconoce los parámetros restantes como la cuenta regresiva y duración de la
  start_count_down, length_count_down = GetCountLength(args)

  # Se inicia la comunicación con el dispositivo :
  card = openCard(port, throughput_limit)

  # Determina la fase de trabajo :
  phase = args[1][-1] if len(args[1]) > 4 else 'L'

  # Comprueba si la fase de trabajo existe en la tarjeta :
  if not phase in card.inputs_available() :
    print('La entrada %s no existe en la tarjeta de modelo %s' %(phase,
                                                   card.id['hardware_model']))
    sys.exit(-1)

  # Se advierte al usuario de las conexiones necesarias :
  print('Calibración de la Fase %s-N (Entrada %s)\n' %(phase, phase))
  if (type(card) == EstCard1V0) or (phase == 'L') :
    print('Las entradas L y N deben estar alimentadas con la tensión ' \
          'nominal \ny simultánemente debe prepararse para medirse con ' \
          'el multímetro.\n')
    if phase != 'L' :
      print('Además la entrada %s debe conectarse con la entrada L' %phase)
      print('y la entrada %s con la entrada N.\n' %('V' if phase == 'S'
                                                                    else 'S'))

  else :
    print('Las entradas L y %s deben estar conectadas entre si, deben\n' \
          'alimentarse con respecto a la entrada N con la tensión nominal\n'\
          'y simultánemente debe prepararse para medirse.\n' % (phase))

  # Realiza la medición y su presentación :
  Measuring(card, phase, start_count_down, length_count_down, ref_measure)

  # Se interroga por el valor de la medición de referencia, solo cuando se
  # calibra la fase L(-N) y no existe un instrumento de referencia conectado :
  if ref_measure is not None :
    Vref = ref_measure.avg

  elif phase == 'L' :
    while True :
       try :
         ans = input('\n\nValor de Referencia : ')
         if ans == 'x' :
           print('\nNo se programo el valor a elección del usuario.')
           sys.exit(0)

         Vref = float(ans)
         break

       except ValueError as e :
         print("Error - Valor numérico inválido, 'x' para "                 \
                                                  "abandonar la calibración.")

       except Exception as e :
         print(repr(e))
  else :
    Vref = card.LN.rms

  # Se invoca al calibrador de la fase, de manera de acceder a la ganancia
  # actual y la nueva, de sus representaciones interna y la medición justo
  #realizada :
  try :
    cal = card.calibrator(phase, Vref)

  except ValueError as e :
    print('Error - No se puede continuar con la calibración.')
    print('%s' %e.message)
    card.close()
    sys.exit(1)

  # Se posponen los cambios ...
  try :
    print('\nEl valor actual %s del factor de calibración de la fase %s, ' \
          '\nse remplazará por (%s) \n' %(cal.old, phase, cal.new))

    while True and not skip :
      ans = input('Se acepta ?  [S/N]')
      if ans.lower() in ['s', 'si', 'n', 'no'] : break

    # y se solicita la autorización para el cambio :
    if skip or (ans.lower() in ['s', 'si']) :
      cal.commit()
      print('\nLa ganancia se reajusto.\n')
    else :
      print('\nNo se programo el valor a elección del usuario.\n')

    card.ExitRemoteMode()

  except OTCProtocolError :
    # En este punto el 'logger' reporto la descripción del error en la
    # consola y no hay nada que hacer.
    pass

  card.close()

  sys.exit(0)



