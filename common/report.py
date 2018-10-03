#!/usr/bin/python
# -*- coding: utf-8  -*-

import sys
import logging


class report :
   parent_logger = None
   console_handler = None

   def __init__(self, parent_logger, filename = 'report.log') :
      """
      Inicializa el sistema de reporte, el cual es dual, dirigido
      a la consola con un reporte sumario de incidencias y uno
      detallado al archivo filename, el que si no se especifica
      tiene el nombre por defecto 'report.log'.
      """
      # Solo se permite un sistema de reporte :
      if report.parent_logger is not None :
         print("report() debe ser invocado una sola vez.")
         sys.exit()

      # Crea la raíz de reporte :
      report.parent_logger = logging.getLogger(parent_logger)
      report.parent_logger.setLevel(logging.DEBUG)

      # Se utilizan dos manejadores, uno para la consola con mensajes de error
      # graves :
      report.console_handler = logging.StreamHandler()
      report.console_handler.setLevel(logging.ERROR)

      # y un segundo para un archivo de texto, con un detalle exhaustivo :
      file_handler = logging.FileHandler(filename, 'w')
      file_handler.setLevel(logging.DEBUG)

      # Se utiliza el mismo formato para ambos manejadores :
      formatter = logging.Formatter('\n%(asctime)s - %(name)s - '
                                          '%(levelname)s :\n   - %(message)s')
      report.console_handler.setFormatter(formatter)
      file_handler.setFormatter(formatter)

      # como parte del reporte :
      report.parent_logger.addHandler(report.console_handler)
      report.parent_logger.addHandler(file_handler)


   @staticmethod
   def getLogger(child_logger = None) :
      """
      Devuelve un logger identificado como parent_logger.child_logger
      Si no se ha creado la instancia de report, el logger se desvia
      a Nulllogging
      """
      if report.parent_logger is None :
         return

      if child_logger is None :
         return logging.getLogger(report.parent_logger.name)
      else :
         return logging.getLogger(report.parent_logger.name + '.' + child_logger)


   @staticmethod
   def consoleSetLevel(value = logging.ERROR) :
      report.console_handler.setLevel(value)

   @staticmethod
   def disable():
     report.parent_logger.setLevel(100)