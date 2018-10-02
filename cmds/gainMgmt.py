#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *


def GainCmd(args, port, throughput_limit) :
  """
  EstApp : Ganancias de Compensación
  ==================================

  La tarjeta mide la tensión de dos fuentes, la primera mide la tensión
  entre las entradas L-N, la segunda dependiendo del modelo mide la tensión
  entre las entradas U-V o U-N. En el primer caso se tienen hasta 3 factores
  de compensación (calibración), para cada una de las fases L, U y V, en el
  segundo solo dos las fase L y U.

  Las ganancias o factores de compensación de las entradas L y U corrigen la
  ganancia de los divisores resistivos asociados a cada una de estas, en el
  caso de existir la entrada de tensión V esta se corrige con respecto al
  divisor de la entrada U.

  El valor nominal de las ganacias es de 50362 para las entradas L y U y
  admite valores entre 65535 y 0. Por otro lado para la entrada V su valor
  nominal es 0 y admite valores entre -128 a 127

  Uso :
     >> EstApp.py -[g|gL|gU|gV] [?]
     >> EstApp.py -[gL|gU|gV] valor_ganancia

  donde gL, gU, gV indican la ganancia de la entrada respecriva (L, U, V),
  el genérico g solo se utiliza para la lectura simultánea de las ganancias
  de las tres entradas.
  """

  card = openCard(port, throughput_limit)

  if (len(args) < 3) or (args[2] == '?') :

    if args[1] == '-g' :
      to_read = ['_gain%s' %x for x in card.inputs_available()]

    elif args[1][-1] in card.inputs_available() :
      to_read = ['_gain' + args[1][-1]]

    else :
      print('Error - El modelo de tarjeta %s no tiene la entrada %s.' %       \
                                      (card.id['hardware_Model'], args[1][-1]))
      sys.exit(1)

    for g in to_read :
      print(' La ganancia %s-N es %d.' %(g[-1], getattr(card, g)))

  else :
    if args[1] == '-g' :
      print('Error - Solo se permite ? para esta opción. ')
      sys.exit(-1)

    try :
      val = int(args[2])
      if (val < 0) or (val > 65535) : raise ValueError()
    except ValueError as e :
      print('Error : El valor %s no es número o esta fuera de rango.' %args[2])

    setattr(card, '_gain' + args[1][-1], val)

    print('  La ganancia de la entrada %s-N se rajusto a %d' %(args[1][-1], val))

  card.close()