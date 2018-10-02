#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
from common import openCard


def ThresholdCmd(args, port, throughput_limit) :
  """
    EstApp : Umbrales de Tensión de los Taps
    ===========================================

    Tiene tres formas :
      (a) Presenta una tabla con la lista de los taps activos :

          >> EstParser.py -u
          o
          >> EstParser.py -u  ?

      (b) Modifica el número de cambios, al valor definido por
          Nuevo_Valor_del_Numero_de_Cambios :

          >> EstParser.py -u total Nuevo_Valor_del_Numero_de_Cambios

      (b) Modifica el valor de un umbral, cuyo número de orden de menor a mayor
          es Nro_de_Orden y cuya posición superior o inferior es indicada por
          Pos con el valor dado por Nuevo_Valor_del_Umbral :

          >> EstParser.py -u  Nro_de_Orden  Pos  Nuevo_Valor_del_Umbral

          El número de orden se indica en forma abreviada, es decir puede ser
          '1ro', '2do', '3ro', '4to', '5to', '6to', '7mo', '8vo', '9no', '10mo',
          '11avo' o '12avo'

          La posición se indica por las palabras 'sup' o 'superior' para el
          valor del umbral de cambio al siguiente tap e 'inf' o'inferior' para
          el valor del umbral al tap anterior.
  """

  num_tap = ['1ro', '2do', '3ro', '4to', '5to', '6to',
                               '7mo', '8vo', '9no', '10mo', '11avo', '12avo']

  card = openCard(port, throughput_limit)

  if (len(args) < 3) or (args[2] == u'?') :
    print(card.threshold)

  elif args[2] == 'total' :
    if (len(args) < 4) or (args[3] == u'?') :
       print('El Número Total de Taps es : %d' %len(card.threshold))
    else :
      try :
        val = int(u' '.join(args[3:]))
      except :
        print('Error : "%s" no es un número.' % args[3:])
        card.close()
        sys.exit(1)

      try :
        card.threshold.len = val
      except ValueError as e :
        print(e.message)
        card.close()
        sys.exit(1)

      print(u'El Número Total de Taps (operativos) se '                     \
                                        u'reajusto a %d' %len(card.threshold))
  elif args[2] in num_tap :
    if not (num_tap.index(args[2]) < len(card.threshold)) :
      print(u'Error : El tap excede el número de taps operativos.')
      card.close()
      sys.exit(1)

    if len(args) < 4 :
      print ('Los Umbrales del tap %s  son :\n  ' % args[2],)
      print (card.threshold[num_tap.index(args[2])])

    else :
      pos = [u'sup', u'superior', u'inf', u'inferior']
      if not args[3].lower() in pos :
        print('Error : %s no indica la posición del umbral '               \
                                      '(sup(erior) o inf(erior)).' % args[3])
        card.close()
        sys.exit(1)

      tap_idx = num_tap.index(args[2])
      if len(args) < 5 :
        print('El Umbral %s del %s tap es %s' %(
                   pos[pos.index(args[3][:3])+1].capitalize(), args[2],
                               getattr(card.threshold[tap_idx], args[3][:3])))
      else :
        try :
          val = float(args[4])
          setattr(card.threshold[tap_idx], args[3][:3], val)
        except Exception as e:
          print("Error : %s no es un número o esta fuera de rango." % args[4])
          card.close()
          sys.exit(1)

        print('Se reajusto el Umbral %s del %s tap a %s' %(
                   pos[pos.index(args[3][:3])+1].capitalize(), args[2],
                               getattr(card.threshold[tap_idx], args[3][:3])))

  else :
    print(u'Error : "%s" no es el índice de un tap o '                      \
                                          u'el sub-comando "total".' %args[2])
    print('Pruebe la opción -h -u para ver los detalles.')
    card.close()
    sys.exit(1)

  card.close()

