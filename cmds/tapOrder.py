#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
#from otcCard.OTCCard import *
#from estCard.EstCard import *
from common import openCard



def OrderingTapCmd(args, port, throughput_limit) :
  """
    EstApp : Configuración del Orden de los Taps
    ============================================

    Uso :
       >> EstApp.py -o
       >> EstApp.py -o nuevo_orden

     La primero orden presenta en la consola el orden de activación de los taps
     cuando la tensión es ascendente.
     La segunda además modifica el orden de los taps, según la secuencia definida
     por nuevo orde.
     
     nuevo_orden se expresa como la secuencia de números, en que es el número de
     la salida (TAPx, x = 1,2,3 ...) en la que se reordena la activación de los 
     taps (siempre cuando la tensión es ascendente). 
     
     Se deben asignar la secuencia de activación a todos los Taps del modelo de 
     la tarjeta, independientemente si no se usan todos los taps.

     Orden válida para Versiones de Software 1V05 o superiores.
  """

  card = openCard(port, throughput_limit)

  #if card.id['software_kernel'] == 'CtrEst 1V0' :
  #  print('Error : Orden no válida para esta la versión de programa de la tarjeta.')
  #  sys.exit(1)

  seq_str = lambda x : ' '.join(['{:d}'.format(n) for n in x])

  std_order = (1,2,3,4,5,6,7,8,9,10,11,12)[:card.tapLimit]
  tap_order = card.tapOrder[:card.tapLimit]

  print(' Orden de los Taps :')
  print(('           %s' % seq_str(std_order)))
  print(('Anterior   %s' % seq_str(tap_order)))

  new_order = [int(n) for n in args[2:]]
  if len(new_order) > 0 :
    if len(new_order) != card.tapLimit :
      print(('Error - El número de taps definido no coincide con el del modelo de tarjeta (%d).' %card.tapLimit))

    elif any([(n < 1) or (n > card.tapLimit) for n in new_order]) :
      print(('Error - El número de órden de los taps excede el rango (1 - %d).' % card.tapLimit))

    elif any([new_order.count(n) > 1 for n in std_order]) :
      for n in std_order :
        if new_order.count(n) > 1:
          print(('Error - El número de órden (%d) de los taps esta repetido.' % n))

    else :
      card.tapOrder = new_order + list(range(card.tapLimit+1 , 12 + 1))
      new_order = card.tapOrder[:card.tapLimit]

      print(('Actual     %s\n' % seq_str(new_order)))
      print('Se cambio el orden de los taps.')

  card.close()
