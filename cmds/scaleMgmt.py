#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard


def ScaleCmd(args, port, throughput_limit) :
  u'''
  EstParser : Escala de Medición de las Tensiones
  ==============================================

  La escala de tensión depende la resistencias asociadas a las entrada de
  tensión alterna y el voltaje de referencia (potenciometro), según las
  fórmulas :
            Vref = 5V * 0.5 * P / (Rs + 0.5*P + k*Rd)
            Scale = Ri / Vref

  donde Rs es la resistencia en serie con el potenciometro (desde el positivo
  de la alimentación de 5V), P  es la resistencia del potenciometro, Rd es el
  valor de las resistencias de los divisores de tensión de la entrada y Ri es
  la resistenica en serie con la entrada de tensión alterna. El factor k es
  2/3 para todos los modelos excepto para el EstCard 23V0 en que es 1.

  El valor programado de la escala se obtiene con la orden
        >> EstParser.py -s

  y se modifica con la orden :
        >> EstParser.py -s nuevo_valor_de_la_escala.
  '''

  card = openCard(port, throughput_limit)

  if (len(args) < 3) or (args[2] == u'?'):
    print('  La Escala de Medición es %1.6f' % card.scale)

  else:
    try:
      scale = float(args[2])
      # if scale < 0 : raise Exception()
    except :
      print("<%s> no es un número.")
      sys.exit(1)

    try:
      card.scale = scale
      print("  Se reajusto la Escala de la Medición a %f" % card.scale)
    except ValueError as e:
      print(e.message)
      card.close()
      sys.exit(1)

  card.close()
