#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *


def GainCmd(args, port, throughput_limit) :
  u"""
    EstParser : Ganancias de Compensación
    =====================================

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
       >> EstParser.py -m [?]
       >> EstParser.py -m nombre_atributo
       >> EstParser.py -m nombre_atributo valor_atributo

    La primera forma permite leer los atributos del modo de operación, que
    son :
     Selección de Entrada :
       Seleccionar la entrada de tensión usada para medir la entrada.
       Admite dos valores LN y UV.

     Realimentación :
       Activa o desactiva la entrada de tensión alternativa para la medicíon
       de la salida. Admite dos valores Actia e Incativa (alternativamente
       on/1 u off/0 respectivamente).

     Expansión :
       Habilita o Deshabilita la salida de expansión. Admite dos valores
       Activa e  Incativa (alternativamente  on/1 u off/0 respectivamente).

     Taps Superpuestos :
       Activa o desactiva el modo de operación de Taps Superpuestos.  Admite
       dos valores Activa e Incativa (alternativamente  on/1 u off/0
       respectivamente).

     Entrada de Coordinación :
     Salida de Coordinación  :
       Activa o desactiva la entrada y salida de coordinación entre tarjetas
       (sistema trifásico). Admite dos valores Activa e Incativa (alternativa-
       mente  on/1 u off/0 respectivamente).

    La segunda forma permite leer el estado de un atributo en particular, donde
    nombre_atributo es cualquiera de los anteriores.

    La tercera forma permite modificar el estado del atributo, en este caso
    valor_atributo, es uno de los valores admisibles.
  """

  card = openCard(port, throughput_limit)

  if (len(args) < 3) or (args[2] == u'?') :

    if args[1] == u'-g' :
      to_read = map(lambda(x) : '_gain%s' %x , card.inputs_available())

    elif args[1][-1] in card.inputs_available() :
      to_read = ['_gain' + args[1][-1]]

    else :
      print u'Error - El modelo de tarjeta %s no tiene la entrada %s.' %  \
                                      (card.id['hardware_Model'], args[1][-1])
      sys.exit(1)

    for g in to_read :
      print ' La ganancia %s-N es %d.' %(g[-1], getattr(card, g))

  else :
    if args[1] == u'-g' :
      print u'Error - Solo se permite ? para esta opción. '
      sys.exit(-1)

    try :
      val = int(args[2])
      if (val < 0) or (val > 65535) : raise ValueError()
    except ValueError as e :
      print u'Error : El valor %s no es número o esta fuera de rango.' %args[2]

    card = openCard(port, throughput_limit)
    setattr(card, '_gain' + args[1][-1], val)

    print u'  La ganancia de la entrada %s-N se rajusto a %d' %(args[1][-1], val)

  card.close()