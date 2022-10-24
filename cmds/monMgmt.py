#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from common import openCard
from estCard.EstCard import *
import queue
import threading
from datetime import datetime
from time import sleep

class RecordReadingTask(threading.Thread) :
  def __init__(self, card, filename) :
    self.card = card
    self.filename = filename

    # Abre el archivo ...
    try :
      self.file = open(filename, 'w')
    except :
      print('El archivo "%s" no se pudo abrir.' %self.filename)

    # y define la cabecera con la identificación del modelo de la tarjeta,
    # escala  y ganancias de las entradas de tensión.
    try :
      self.file.write('# Modelo       : %s\n' %card.id['hardware_model'])
      self.file.write('# Escala       : %s\n' % card.scale)
      for g in map(lambda x : '_gain%s' %x , card.inputs_available()) :
        self.file.write('# Ganancia %s-N : %d\n' %(g[-1], getattr(card, g)))
      self.file.write('# Hora         : %s\n#\n' % str(datetime.now()))
      self.file.write('#  TAP   V(L-N)   V(U-V) \n')

    except :
      print("No se pudo escribir en el archivo de registro.")
      sys.exit(1)

    # Se prepara el hilo de ejecución, para su arranque :
    threading.Thread.__init__(self)

    self.setDaemon(True)
    self.started = False

  def run(self) :
    self.started = True
    while self.started :
      if not self.card.measure.queue.empty() :
        measure = self.card.measure.queue.get()
        try  :
          self.file.writelines('%5d,%8d,%8d\n' %(measure[0], measure[1],
                                                                measure[2]))
        except :
          print("No se pudo escribir en el archivo de registro.")
          break
      sleep(0.001)

    self.file.close()

  def stop(self) :
    self.started = False


def MonCmd(args, port, throughput_limit) :
  u"""
    EstApp : Monitor de Tensión
    ===========================

    Uso :
      >> EstApp.py -mon [log_file]

    Presenta en la consola la medición y las estadísticas básicas de las
    tensiones LN y UV, a una taza de 1 seg.

     Simultáneamente registra el resultado en el archivo log_file (por
     defecto 'cycle_sampling.csv') de cada lectura.


  """

  card = openCard(port, throughput_limit)

  # Verifica los parámetros de trabajo :

  filename = args[2] if len(args) > 2 else 'cycle_sampling.csv'
  record_task = RecordReadingTask(card, filename)

  print('El registro de muestreo por ciclo se almacenará en %s\n' %filename)

  try :
    card.StartMeasure()
  except Exception as e :
    card.close()
    if type(e) != OTCProtocolError : print(e)
    sys.exit(1)

  record_task.start()

  if not card.measure.is_alive() :
    print( 'Measure thread is not alive')

  try :
    while card.measure.is_alive() :
      sleep(1.000)

      # Captura las lecturas de tensión :
      vLN = str(card.LN)
      vUV = str(card.UV)

      # Se requiere que las estádisticas no sean acumuladas en todo el
      # periodo de medición, sino con cada lectura :
      card.LN.stats.arm()
      card.UV.stats.arm()

      # Presenta los resultados en la consola :
      print('[L-N] %s, [U-V] %s, [%2d]' %(vLN, vUV, card.LN.stats._count))

  except KeyboardInterrupt :
      pass

  record_task.stop()
  card.close()
