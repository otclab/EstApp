#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *


def ModeCmd(args, port, throughput_limit) :
  u"""
    EstParser : Atributos del Modo de Operación
    ===========================================

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


  # Si no se especifican argumentos adicionales, se presentan todas las
  # funciones del Modo :
  if (len(args) < 3) or (args[2] == u'?') :
    card = openCard(port, throughput_limit)
    print u'Las Funciones del Modo de Operación\nestán programadas según :\n'
    print u'%s' %card.modeFlags

    sys.exit(0)

  card = openCard(port, throughput_limit)

  # Como el nombre de la función del modo, es en general compuesta por mas de
  # de una palabra, su nombre estará definido por la concatenación de los
  # elementos de args desde el tercero (i.e.args[2]) hasta un número determi-
  # nado por el nombre mismo. Para identicarlo los elementos de args a partir
  # del tercero se concatenan para fomrar tuplas (nombre, valor) :
  #    name[n] = args[2] + ' ' + ... args[2+n]
  #   valor[n] = args[2+n+1] + ' ' + ... args[len(args) - 3]
  # y se prueban hasta encontrar la que sea correcta.
  name_value = [(u' '.join(args[2:3+n]), u' '.join(args[3+n:]))
                                                   for n in range(len(args))]

  # Es conveniente trabajar con los nombres en minúscula, flag_namens es un
  # diccionario que contiene los nombres estándar de las banderas vs el
  #nombre en minúscula :
  flag_names = dict([(n.lower(), n) for n in ModeFlags.functionNames()])

  for name, value in name_value :
    if name.lower() in flag_names.keys() :
      # Obtiene el nombre real :
      name = flag_names[name.lower()]

      if value in [u'?', u''] :
        print u'Estado de la función de %s' %card.modeFlags.getStatusStr(name)
        card.close()
        return

      else :
        try :
          setattr(card.modeFlags, card.modeFlags.getFunctionOf(name), value)

          print u'La función de \'%s\' se modifico a %s' %(name,
                   getattr(card.modeFlags, card.modeFlags.getFunctionOf(name)))
          card.close()
          return

        except ValueError as e :
          print u'%s' % e.message
          card.close()
          sys.exit(1)


  # Si se alcanza este punto la línea e argumentos no pudo ser reconocida :
  print u'Error : "%s" no tiene el formato correcto.'%(args[2:])
  print u'Pruebe la opción -h -m para ver los detalles.'
  sys.exit(1)

