#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from otcCard.OTCCard import *
from estCard.EstCard import *
from common import openCard



def SetTapCmd(port, throughput_limit) :
  """
    EstParser : Operación Manual de los Taps
    ========================================

    Uso :
       >> EstParser.py -manual

    La tarjeta es puesta en el modo de control remoto (deja de regular), perma-
    neciendo con el Tap activo al momento de la invocación de este comando.
    A continuación se inicia una sesión iteractiva, en la que se interroga por
    el tap a activar, el cual es un valor númerico, que si es válido, ordena el
    cambio al tap respectivo en la tarjeta. La sesión se termina cuando se
    responde 'x'.

    La numeración de los taps es a partir de 1, hasta la capacidad (total)de la
    tarjeta. Ordenados de mayor realación al de menor relación.

  """

  card = openCard(port, throughput_limit)
  card.EnterRemoteMode()

  while True:
    try:
      tap_str = input('\nTap a Activar : ')

      if tap_str == 'x':
        print('\nFin.')
        break

      tap = int(tap_str)

      if (tap < 0) or (tap > card.tapLimit):
        print('El número de tap debe ser > 0 y < %d.' % card.tapLimit)
        continue

    except ValueError as e:
      print("Valor numérico inválido, 'x' para abandonar.")

    except Exception as e:
      print(repr(e))

    # TODO Esta no es la mejor solución, el código del uC debe reformarse para
    # que en contol remoto tap = 0 implique la desconexión de todos los Taps.
    if tap != 0:
      # [TO DO]La siguiente instrucción fuerza el borrado de las banderas de
      # Sobrevoltaje y Subvoltaje, si se comenta la activación de los taps
      # solo puede efectuarse con la tensión de entrada en el rango correcto.
      #card.set('Tap Flags', 4)

      card.set('Tap Activo', tap + 0x0400)
      print('Se Activo el tap %d.' % tap)
    else :
      #card.set('Tap Flags', 5)
      card.set('Tap Activo', tap + 0x0500)
      print('Se desactivaron todos los Taps.')

  card.ExitRemoteMode()
  card.close()

