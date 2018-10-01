#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard


def TimersCmd(args, port, throughput_limit) :
  u"""
    EstParser : Tiempos de Encendido y Corte
    ========================================

    Uso :
       >> EstParser.py -t [?]
       >> EstParser.py -t [ off | corte | apagado | on | encendido ]
       >> EstParser.py -t tipo tiempo [por] [subtension | sobretension]
       >> EstParser.py -t tipo tiempo [por] tipo_evento Valor_del_Tiemo


    Permite leer los tiempos de corte y encendido por y desde sobretensión y
    subtensón.

    La primera forma presenta dodos los tiempos, la segunda los restringe
    según el tipo de tiempo, i.e. solo a los de corte (opciones off, corte,
    apagado),  o solo a los de encendido (opciones on, encendido).

    La tercera restringe la presentación a un solo tiempo, donde tipo tiempo
    es cualquiera de las opciones [ off | corte | apagado | on | encendido] y
    el tercer argumento define el evento que se temporiza (subtensión o sobre-
    tensiòn).

    La cuarte es similar a la tercera pero ajusta el valor del tiempo por el
    especificado en Valor_del_Tiempo, el cual debe ser el valor númerico del
    tiempo expresado en segundos.

  """

  if (len(args) < 3) or (args[2] == u'?'):
    card = openCard(port, throughput_limit)
    for s1 in [u'Apagado por', u'Encendido desde'] :
      for s2 in [u'Subtensión', u'Sobretensión'] :
        t_name = u'Tiempo de %s %s' %(s1,s2)
        print u'  %-38s = %0.1f seg' %(t_name, card.get(t_name)/60)

    card.close()

  elif args[2].lower() in [u'corte', u'apagado', 'off'] :
    t_name = u'Tiempo de Apagado por '

  elif args[2].lower() in [u'encendido', u'on'] :
    t_name = u'Tiempo de Encendido desde '

  else :
    print u'Error : "%s" no es una opción correcta.' % args[2]
    print u'Pruebe la opción -h -t para ver los detalles.'
    sys.exit(1)

  if (len(args) > 3) and (args[3] in [u'por', u'desde']) :
    args.pop(3)

  if (len(args) < 4) or (args[3] == u'?') :
    card = openCard(port, throughput_limit)
    s1 = t_name
    for s2 in [u'Subtensión', u'Sobretensión'] :
      t_name = u'%s%s' %(s1,s2)
      print u'  %-38s = %0.1f seg' %(t_name, card.get(t_name)/60)
    card.close()

  elif args[3].lower() == u'subtension' :
    t_name += u'Subtensión'

  elif args[3].lower() == u'sobretension' :
    t_name += u'Sobretensión'

  else :
    print u'Error : "%s" no es una opción correcta.' % args[3]
    print u'Pruebe la opción -h -t para ver los detalles.'
    sys.exit(1)

  if (len(args) < 5) or (args[4] == '?') :
    card = openCard(port, throughput_limit)
    val = card.get(t_name)
    print u'%s = %0.1f seg.' %(t_name, val/60)
    card.close()

  else :
   try :
     val = float(args[4])
   except :
     print u"Error : %s no es un número." % args[4]
     sys.exit(1)

   if (val < 0) or (val > 65535/60) :
     print u"Error : %s esta fuera de rango [0 a %6.2f seg.]." % (args[4],
                                                                    65535/60)
     sys.exit(1)

   card = openCard(port, throughput_limit)
   card.set(t_name, int(val*60))
   card.close()

   print u"Se reajusto el %s a %0.1f seg." %(t_name, val)

