#!/usr/bin/python
# -*- coding: utf-8 -*-

# IntelHex

# Formato IntelHex :
# Esta formado por un secuencia de líneas con el siguiente formato :
#
#     ':' c[0][0] c[0][1]  ...    c[n-1][0] c[n-1][1]
#
# donde c[][] representan los caracteres ASCII de digitos hexadecimales,
# cada par (c[i][0], c[i][1]) forman la representación hexadecimal del
# byte b[i], i = 0 ... n-1, los cuales forman los siguientes campos del
# registro :
#     b[0]             : RECLEN
#     b[1], b[2]       : LOAD OFFSET (MSB y LSB respectivamente)
#     b[3]             : RECTYPE
#     b[4],..., b[n-2] : INFO/ULBA/USBA/CSIP/EIP
#     b[n-1]           : CHKSUM
#
# RECLEN define el número de bytes del campo INFO/ULBA/USBA/CSIP/EIP.
#
# LOAD OFFSET define la dirección (relativa) inicial de los bytes de
# datos (i.e. b[4], ...), solo es significativo en el registro del
# tipo 'Data Record', en cualquier otro tipo debe ser cero (0x0000).
#
# RECTYPE define el tipo de registro y con ello el significado del
# campo INFO/ULBA/USBA/CSIP/EIP según :
#  Data Record (8-, 16-, or 32-bit formats) : RECLEN = 0
#     En este caso son los bytes definidos a partir de la dirección
#     relativa LOAD OFFSET y hasta la dirección LOAD OFFSET + RECLEN
#     - 1.
#
#  End of File Record (8-, 16-, or 32-bit formats) : RECLEN = 1
#     Especifica el final de los registros, no contiene el campo
#     INFO/ULBA/USBA/CSIP/EIP, por lo cual es un campo de estructura
#     definida (aka. ':00000001FF').
#
#  Extended Segment Address Record (16- or 32-bit formats) : RECLEN = 2
#     Usado para especificar el 'Upper Segment Base Address' (USBA),
#     aka los bits 4-19 del dirección base del segemnto (SBA, Segment
#     Base Address).
#
#  Start Segment Address Record (16- or 32-bit formats) : RECLEN = 3
#     Usado para especificar la dirección de ejecución en el modo
#     real (utilizando los registros CS/IP) , mediante el campo
#     INFO/ULBA/USBA/CSIP/EIP el cual es de 4 bytes.
#
#  Extended Linear Address Record (32-bit format only) : RECLEN = 4
#     INFO/ULBA/USBA/CSIP/EIP es de dos bytes y especifica los bits
#     16 a 31 de la dirección base lineal (LBA, Linear Base Address)
#     denominados ULBA (Upper Linear Base Address), desde la que se
#     ubicarán los datos de los registros subsiguientes.
#
#  Start Linear Address Record (32-bit format only) : RECLEN = 5
#     Usado para especificar la dirección de ejecución en el modo
#     no real o EIP, mediante el campo INFO/ULBA/USBA/CSIP/EIP el
#     cual es de 4 bytes bytes.
#
#  En la practica los registros del tipo Extended Segment Address
#  Record (2), Start Segment Address Record (3) y Start Linear
#  Address Record (5) son especificos de la arquitectura 8086.
#
#  La mayoría de fabricantes adapta solo el espacio de memoria
#  Lineal, de manera que la dirección esta formada por los 16
#  bits inferiores especificados por el campo LOAD OFFSET de
#  (el/los) registros de datos (Data Record) y los 16 bits
#  superiores del último registro de definición ULBA (Extended
#  Linear Address Record).
#
# Microchip asigna el contenido de la EEPROM a partir de la
# dirección 0x0001E000, como ejemplo del volcado :
#
# :020000040001F9
# :10E00000B4000000B4000000B4000000B400000040
# :10E0100004000000BA00C400BA00C40000003100CF
# :10E020002E00370030003600300031003000000094
# :10E030000000000000000000000000000000CF0011
# :10E0400045005B0035002E005000230044006200B4
# :10E050005B00A8004D0000006A005100590000005C
# :10E060006A005100590000006A0051005900000088
# :10E070006A005100590000006A0051005900000078
# :10E080006A005100590000006A0051005900000068
# :10E090006A005100590000006A0051005900000058
# :10E0A0006A0051005900FF00FF00FF00FF00FF0061
# :10E0B000FF00FF00FF00FF00FF00FF00FF00FF0068
# :10E0C000FF00FF00FF00FF00FF00FF00FF00FF0058
# :10E0D000FF00FF00FF00FF00FF00FF00FF00FF0048
# :10E0E000FF00FF00FF00FF00FF00FF00FF00FF0038
# :10E0F000FF00FF00FF00FF00FF00FF00FF00FF0028
# :10E10000FF00FF00FF00FF00FF00FF00FF00FF0017
# :10E11000FF00FF00FF00FF00FF00FF00FF00FF0007
# :10E12000FF00FF00FF00FF00FF00FF00FF00FF00F7
# :10E13000FF00FF00FF00FF00FF00FF00FF00FF00E7
# :10E14000FF00FF00FF00FF00FF00FF00FF00FF00D7
# :10E15000FF00FF00FF00FF00FF00FF00FF00FF00C7
# :10E16000FF00FF00FF00FF00FF00FF00FF00FF00B7
# :10E17000FF00FF00FF00FF00FF00FF00FF00FF00A7
# :10E18000FF00FF00FF00FF00FF00FF00FF00FF0097
# :10E19000FF00FF00FF00FF00FF00FF00FF00FF0087
# :10E1A000FF00FF00FF00FF00FF00FF00FF00FF0077
# :10E1B000FF00FF00FF00FF00FF00FF00FF00FF0067
# :10E1C000FF00FF00FF00FF00FF00FF00FF00FF0057
# :10E1D000FF00FF00FF00FF00FF00FF00FF00FF0047
# :10E1E000FF00FF00FF00FF00FF00FF00FF00FF0037
# :10E1F000FF00FF00FF00FF00FF00FF00FF00FF0027
# :00000001FF
#
# El cual se puede generar por ejemplo con :
#   BuildRecord(ulba = 0x0001)
#   BuildRecord(offset = 0xE000, data = 0xB4, 0x00, 0x00, 0x00,
#                            0xB4, 0x00, 0x00, 0x00, 0xB4, 0x00,
#                             0x00, 0x00, 0xB4, 0x00, 0x00, 0x00)
#   BuildRecord(offset = 0xE010, data = 0x04, 0x00, 0x00, 0x00,
#                            0xBA, 0x00, 0xC4, 0x00, 0xBA, 0x00,
#                             0xC4, 0x00, 0x00, 0x00, 0x31, 0x00)
#   . . .
#   BuildRecord()
#
#
#
# Formato MCH :
# Formato de exportación/importación de Microchip, los bytes del contenido se
# codifican por su representación hexadecimal (sin el prefijo 0x, ni posfijo h)
# consecutivamente en cada linea del archivo. No exite especificación adicional,
# ni siquiera de la dirección de inicio.

def BuildRecord(**farg) :
   """
   Devuelve un registro en el fomato IntelHex, puede invocarse de las
   siguientes maneras :
      (1) Data Record : BuildRecord(data = byte_list, offset = load_offset)
            Devuelve un registro de datos, donde load_offset especifica el
            offset del registro y byte_list la lista de bytes del registro,
            cada byte se representa por un entero acotados al rango de 0 a
            255.
      (2) End of File Record : BuildRecord()
            Sin argumentos devuelve el registro final.
      (3) Extended Segment Address Record : BuildRecord(usba = usba_val)
      (4) Start Segment Address Record : BuildRecord(csip = csip_val)
      (5) Extended Linear Address Record : BuildRecord(ulba = ulba_val)
      (6) Start Linear Address Record : BuildRecord(eip = eip_val)

   ulba_val y usba_val son enteros acotados en el rango 0 a 0xFFFF (16 bits),
   eip_val y csip_val son enteros acotados en el rango de 0 a 0xffffffff (32
   bits).
   """

   # Se procesan los argumentos de invocación de la función para definir los
   # campos load_offset, rectype e info :
   if len(farg.keys()) == 0 :
      # End of File Record :
      load_offset = 0
      rectype = 1
      info = []

   elif len(farg.keys()) == 1 :
      if 'usba' in farg.keys() :
         if isinstance(farg['usba'], (int, long)) :
            # Extended Segment Address Record (16- or 32-bit formats)
            if (farg['usba'] >= 0) and (farg['usba'] <= 0xFFFF) :
               load_offset = 0
               rectype = 2
               info = [farg['usba'] % 256, farg['usba'] // 256]
            else :
               raise ValueError("'usba' fuera de rango.")
         else :
            raise TypeError("'usba' debe ser del tipo int.")

      elif 'ulba' in farg.keys() :
         # Extended Linear Address Record (32-bit format only)
         if isinstance(farg['ulba'], (int, long)) :
            if (farg['ulba'] >= 0) and (farg['ulba'] <= 0xFFFF) :
               load_offset = 0
               rectype = 4
               info = [farg['ulba'] % 256, farg['ulba'] // 256]
            else :
               raise ValueError("'ulba' fuera de rango.")
         else :
            raise TypeError("'ulba' debe ser del tipo int.")

      elif 'csip' in farg.keys() :
         # Start Segment Address Record (16- or 32-bit formats)
         if isinstance(farg['csip'], (int, long)) :
            if (farg['csip'] >= 0) and (farg['csip'] <= 0xFFFFFFFF) :
               load_offset = 0
               rectype = 3
               info = []
               for i in range(0,4) :
                  info += [farg['csip'] % 256]
                  farg['csip'] = farg['csip'] // 256
            else :
               raise ValueError("'csip' fuera de rango.")
         else :
            raise TypeError("'csip' debe ser del tipo int/long.")

      elif 'eip' in farg.keys() :
         # Start Linear Address Record (32-bit format only)
         if isinstance(farg['eip'], (int, long)) :
            if (farg['eip'] >= 0) and (farg['eip'] <= 0xFFFFFFFF) :
               load_offset = 0
               rectype = 5
               info = []
               for i in range(0,4) :
                  info += [farg['csip'] % 256]
                  farg['csip'] = farg['csip'] // 256
            else :
               raise ValueError("'eip' fuera de rango.")
         else :
            raise TypeError("'eip' debe ser del tipo int/long.")

      elif 'data' in farg.keys() :
         raise TypeError("Falta el valor del argumento 'offset'.")

      elif 'offset' in farg.keys() :
         raise TypeError("Falta el valor del argumento 'data'.")

      else :
         raise TypeError("El argumento '%s' no es válido", farg.keys()[0])

   elif len(farg.keys()) == 2 :
      if ('data' in farg.keys()) and  ('offset' in farg.keys()) :
         # Data Record (8-, 16-, or 32-bit formats) :
         rectype = 0

         load_offset = farg['offset']
         if not isinstance(load_offset, (int, long)) :
            raise TypeError("'offset' debe ser del tipo int/long.")

         info = farg['data']

         if not isinstance(info, list) :
            raise TypeError("'data' debe ser una lista (de bytes).")

         for i in range(0, len(info)) :
            if not isinstance(info[i], (int,long)) :
               raise TypeError("El %d-esimo valor de 'data' contiene un valor del tipo invalido (no 'int/long')." % i)
            if (info[i] < 0) or (info[i] > 255) :
               raise TypeError("El %d-esimo valor de 'data' contiene un valor fuera de rango." % i)

      else :
         raise TypeError("Uno o mas de los argumentos no son validos.")

   else :
      raise TypeError(" Demasiados argumentos.")

   # Se construye el registro, iniciandose por el marcador inicial :
   record = ':'

   # Se añade la longitud (del campo info) del registro, representado por su
   # representación hexadecimal (sin el prefijo '0x', ni posfijo 'h') :
   record += '{0:02X}'.format(len(info))

   # Se añade el valor del campo offset :
   record += '{0:04X}'.format(load_offset)

   # Se añade el campo del tipo de registro :
   record += '{0:02X}'.format(rectype)

   # Se convierte la lista de bytes a la lista de sus representaciones hexadecimales
   record += "".join(['{0:02X}'.format(b) for b in info])

   # Se calcula la suma de verificación ...
   chksum = 256 - ((len(info) + (load_offset//256) + (load_offset % 256) + rectype + sum(info)) % 256)

   # y finalmente se añade al registro para completarlo :
   record += '{0:02X}'.format(chksum)

   return record


# Valores del Identificador del tipos de registro :
RecordTypeDict = {'data' : 0, 'end_of_file' : 1, 'usba' : 2, 'csip' : 3, 'ulba' : 4, 'eip' : 5}

def WordAt(list_bytes, idx) :
   if type(list_bytes) == 'list' :
      val = list_bytes[idx]*256 + list_bytes[idx+1]
   return val


def DWordAt(list_bytes, indx) :
   if type(list_bytes) == 'list' :
      val = long(list_bytes[idx]*256 + list_bytes[idx+1])*65536
      val += list_bytes[idx+2]*256 + list_bytes[idx+3]
   return val

def BytesOf(val, len) :
   list_bytes = [0]*len
   for i in range(1, len+1) :
      list_bytes[-i] = val % 256
      val = (val//256)
   return list_bytes

def IsListofBytes(L) :
   return (isinstance(L, (list, tuple)) and
            all([isinstance(x, (int)) and (x >= 0) and (x < 256) for x in L]))


class IntelHexRecord(object) :
   '''
   Clase base para la representación paramétrica de los registros IntelHex.
   '''
   def __init__(self) :
      self.typ = None
      self.offset = 0
      self.info = []

   def __str__(self) :
      '''
      Devuelve la representación en el formato IntelHex del registro.
      '''
      chksum = 256 - ((len(self.info) + (self.offset//256) + (self.offset % 256) +
                              RecordTypeDict[self.typ] + sum(self.info)) % 256)

      return ':' +                                                  \
             '{0:02X}'.format(len(self.info)) +                     \
             '{0:04X}'.format(self.offset) +                        \
             '{0:02X}'.format(RecordTypeDict[self.typ]) +           \
             ''.join(['{0:02X}'.format(b) for b in self.info]) +    \
             '{0:02X}'.format(chksum)

   @staticmethod
   def __parse_record(rec_txt) :
      '''
      Interpreta el texto importado como un registro IntelHex, devuelve un
      registro de la subclase de IntelHexRecord correspondiente.
      '''
      if (len(rec_txt) == 0) or (rec_txt[0] != ':') :
         raise ValueError(u'El registro no se inicia con el caracter ":".')

      # Elimina los espacios en blanco al final del texto del registro :
      rec_str = rec_txt.rstrip()

      # Separa los caracteres que definen los bytes del formato ...
      bytes_str = [rec_txt[i:i+2] for i in range(1, len(rec_str.rstrip()), 2)]

      # y los convierte a sus valores :
      try :
         bytes = list(map(int, bytes_str, [16 for i in range(0, len(bytes_str))]))
      except ValueError as e :
         raise ValueError(u'%s no puede interpretarse como un byte' % e.args[0][-5:-1])

      # Verifica que el registro defina el mínimo de bytes requeridos :
      if len(bytes) < 5 :
         raise ValueError(u'El registro es muy corto.')

      # Identifica los campos del registro :
      rec_len = bytes[0]
      offset = bytes[1]*256 + bytes[2]

      try :
         typ = [typ for typ, id in RecordTypeDict.items() if id == bytes[3]][0]
      except IndexError as e :
         raise ValueError(u'El byte de tipo %02X es inválido.')

      info = bytes[4 : len(bytes) - 1]
      chksum = bytes[-1]

      # Verifica que la longitud del registro sea coherente con la carga del
      # registro :
      if rec_len != len(info) :
         ValueError(u'La longitud del registro no es coherente.')

      # Verifica que el registro final tenga el formato correcto :
      if (typ == END_RECTYPE) and ((len(info) != 0) or
                                      (offset != 0) or (chksum != 0xFF)) :
         raise ValueError('Registro \'End_of_File\' con mal formato.')

      # Verifica la suma de verificación :
      if (sum(bytes) % 256) != 0 :
         raise ValueError('La suma de verificación es incorrecta.')

      # [TO DO] Comprobar que los registros del tipo ISBA y ULBA tienen el formato correcto

      if typ == 'data' :
         return DataRecord(offset, info)

      else :
         if offset != 0 :
            raise ValueError(u'El campo Load Offset debe ser 0 para este tipo de registro.')

         if typ == 'ulba' :
            if len(info) != 2 :
               raise ValueError(u'En los registros del tipo ULBA el campo info/load debe contener 2 bytes')
            return UlbaRecord(WordAt(info, 0))

         elif typ == 'usba' :
            if len(info) != 2 :
               raise ValueError(u'En los registros del tipo USBA el campo info/load debe contener 2 bytes')
            return UsbaRecord(WordAt(info, 0))

         elif typ == 'csip' :
            if len(info) != 4 :
               raise ValueError(u'En los registros del tipo CSIP el campo info/load debe contener 4 bytes')
            return CsipRecord(info)

         elif typ == 'eip' :
            if len(info) != 4 :
               raise ValueError(u'En los registros del tipo EIP el campo info/load debe contener 4 bytes')
            return EipRecord(info)

         elif typ == 'end_of_file' :
            if len(info) != 0 :
               raise ValueError(u'En los registros del tipo End Of File el campo info/load debe estar vacio (no contiene ningún byte).')
            return EndRecord()


   @staticmethod
   def parse(txt) :
      '''
      Interpreta el texto importado como una lista de registros IntelHex,
      devuelve la lista de registros de la subclase de IntelHexRecord
      correspondientes.
      '''
      record_list = []
      line_list = txt.splitlines()
      rec_typ = None
      line_num = 0
      for line in line_list :
         line_num += 1
         # Se verifica si la linea debe ser ignorada :
         if (len(line) == 0) or (line[0] in [';','#']) or (line[0:2] == '//')  or (line.strip() == '') :
            continue
         try :
            record_list.append(IntelHexRecord.__parse_record(line))
         except ValueError as e :
            raise ValueError(u'INTELHEX Error en la linea %d : %s' %(line_num, e))

      return record_list

# [TO DO] : Verificar que los argumentos sean del tipo válido.
class EndRecord(IntelHexRecord) :
   '''
   Clase de los registros IntelHex (IntelHexRecord) del tipo 'End of File'
   '''
   def __init__(self) :
      IntelHexRecord.__init__(self)
      self.typ = 'end_of_file'


class UlbaRecord(IntelHexRecord) :
   '''
   Clase de los registros IntelHex (IntelHexRecord) del tipo 'ULBA',
   (Upper Linear Base Address).
   '''
   def __init__(self, ulba) :
      IntelHexRecord.__init__(self)
      self.typ = 'ulba'

      if type(ulba) in [int] :
         self.info = BytesOf(ulba, 2)

      elif IsListofBytes(ulba) and (len(ulba) == 2) :
         self.info = [ulba[0]]
         self.info.append(ulba[1])

      else :
         raise ValueError(u'UlbaRecord.__init__ invocado con un argumento de tipo inválido (%s).' % type(ulba))

   def adr(self) :
      return WordAt(self.info, 0)


class UsbaRecord(IntelHexRecord) :
   '''
   Clase de los registros IntelHex (IntelHexRecord) del tipo 'USBA',
   (Upper Segment Base Address).
   '''
   def __init__(self, usba) :
      IntelHexRecord.__init__(self)
      self.typ = 'usba'

      if type(usba) in [int] :
         self.info = BytesOf(usba, 2)

      elif IsListofBytes(usba) and (len(usba) == 2) :
         self.info = [usba[0]]
         self.info.append(usba[1])

      else :
         raise ValueError(u'UsbaRecord.__init__ invocado con un argumento de tipo inválido.')

   def adr(self) :
      return WordAt(self.info, 0)


class DataRecord(IntelHexRecord) :
   '''
   Clase de los registros IntelHex (IntelHexRecord) del tipo 'Data Record'.
   '''
   def __init__(self, offset, data, length = None) :
      IntelHexRecord.__init__(self)
      self.typ = 'data'

      if not type(offset) in [int] :
         raise ValueError(u'DataRecord.__init__, el primer argumento de un tipo inválido.')
      self.offset = offset

      if IsListofBytes(data) :
         if (length is not None) and not (type(length) in [int]) :
            raise ValueError(u'DataRecord.__init__, el tercer argumento de un tipo inválido.')

         if length is None : length = len(data)

         if  length > 256 :
            raise ValueError(u'DataRecord.__init__ el tamaño de la lista de datos es demasiado grande.')

         self.info = data[0:length]

      else :
         raise ValueError(u'DataRecord.__init__ invocado con el segundo argumento de un tipo inválido.')


class CsipRecord(IntelHexRecord) :
   def __init__(self, csip) :
      IntelHexRecord.__init__(self)
      self.typ = 'csip'

      if type(csip) == dict :
         self.info = BytesOf(csip['cs'])
         self.info.append(BytesOf(csip['ip']))

      elif type(csip) in [int] :
         self.info = BytesOf(csip, 4)

      elif IsListofBytes(eip):
         self.info = csip[0:4]
         self.info = ([0]*(4 - len(csip)) + csip)

      else :
         raise ValueError(u'CsipRecord.__init__ invocado con un argumento de tipo inválido.')


class EipRecord(IntelHexRecord) :
   def __init__(self, csip) :
      '''

      '''
      IntelHexRecord.__init__(self)
      self.typ = 'eip'

      if (type(eip) == dict) and (eip.keys() or ('cs','ip')) == ('cs','ip') :
         self.info = BytesOf(eip['cs'])
         self.info.append(BytesOf(eip['ip']))

      elif type(eip) in [int] :
         self.info = BytesOf(eip, 4)

      elif IsListofBytes(eip):
         self.info = eip[0:4]
         self.info = ([0]*(4 - len(eip)) + eip)

      else :
         raise ValueError(u'EipRecord.__init__ invocado con un argumento de tipo inválido.')


class BytesRange(object) :
   '''
   Contenedor de una secuencia continua de bytes.
   '''
   def __init__(self, base_adr, rec) :
      if not(type(base_adr) in [int]) or (base_adr < 0):
         raise ValueError(u'BytesRange.__init__ : Primer argumento no es un número entero no negativo.')

      if IsListofBytes(rec) :
            self.start = base_adr
            self.end   = self.start + len(rec) - 1
            self.bytes = rec

      elif type(rec) == DataRecord :
         self.start = base_adr + rec.offset
         self.end   = self.start + len(rec.info) - 1
         self.bytes = rec.info

      else :
         raise ValueError(u'BytesRange.__init__ : El segundo argumento no es un registro o lista/tupla de bytes.')


   def Append(self, bytes_range) :
      if type(bytes_range) != BytesRange :
         raise ValueError(u'BytesRange.Append : El argumento es de un tipo inválido.')
      self.bytes.extend(bytes_range.bytes)
      self.end = bytes_range.end

   def IsPriorAdjacent(self, bytes_range) :
      if type(bytes_range) != BytesRange :
         raise ValueError(u'BytesRange.Append : El argumento es de un tipo inválido.')
      return (self.end == (bytes_range.start - 1))

   def IsPostAdjacent(self, bytes_range) :
      if type(bytes_range) != BytesRange :
         raise ValueError(u'BytesRange.Append : El argumento es de un tipo inválido.')
      return (bytes_range.end == (self.start - 1))

   def IsOverlaping(self, bytes_range) :
      if type(bytes_range) != BytesRange :
         raise ValueError(u'BytesRange.Append : El argumento es de un tipo inválido.')
      return ((self.start >= bytes_range.end) and (bytes_range.start >= self.end))

   def IsPreceding(self, bytes_range) :
      if type(bytes_range) != BytesRange :
         raise ValueError(u'BytesRange.Append : El argumento es de un tipo inválido.')
      return (self.start < bytes_range.start)

class BytesBlock(object) :
   '''
   Contenedor de secuencias de bytes.
   '''
   def __init__(self, adr = None) :
      self.base_adr = adr
      self.data = []

   # TO DO : si rec es una lista de bytes debe incluirse como argumento adicional
   # el offset
   def add(self, rec) :
      if self.base_adr is None :
         raise ValueError('BytesBlock.add invocada sin haber definido la dirección base.')

      if IsListofBytes(rec) :
         raise ValueError('[TO DO] : BytesBlock.add invocada con una lista de bytes,\n debe incluirse el offset.')

      # Se calcula el rango de direcciones que cubre el registro :
      new_data = BytesRange(self.base_adr, rec)

      if self.data == [] :
         self.data = [new_data]

      else :
         for i in range (len(self.data)) :
            if new_data.IsPostAdjacent(self.data[i]) :
                self.data[i].Append(new_data)
                if (i+1) < len(self.data) :
                   if self.data[i].IsOverlaping(self.data[i+1]) :
                      raise ValueError('Los registros se sobreponen.')

                   if self.data[i+1].IsPostAdjacent(self.data[i]) :
                      self.data[i].Append(self.data.pop(i+1))
                return

            elif self.data[i].IsOverlaping(self.data[i]) :
               raise ValueError('Los registros se sobreponen.')

            elif new_data.IsPreceding(self.data[i]) :
              break ;

         if self.data[i].IsPostAdjacent(new_data) :
            new_data.Append(self.data[i])
            self.data[i] = new_data
         else :
            self.data.insert(i, new_data)


# [TO DO] : Clase IntelHex
# Creación y Adición de contenido de memoria.
# Creación y Adición de una secuencia de registros Intelhex (IntelHexRecord)
#
#
#
#
class IntelHex(object) :
   '''
   Clase de soporte para la traducción y/o generación de texto en formato
   IntelHex y el contenido de memoria (lineal y virtual) que representa
   (adicionalmente de las direcciones de arranque lineal y virtual).
   '''
   def __init__(self, arg1, arg2 = None) :
      self.ulba = BytesBlock()
      self.usba = BytesBlock()
      self.csip = None
      self.eip  = None

      if type(arg1) == list :
         if not all(isinstance(x, IntelHexRecord) for x in arg1) :
            raise ValueError('Error : Algunos elementos del primer argumento no son registros IntelHex.')
         records = arg1

      elif type(arg1) == str :
         # Se identifican los registros del texto, para obtener la representación
         # paramétrica de todos :
         records = IntelHexRecord.parse(txt)

      self.addRecords(records)

   def addULBAbytes(arg1, arg2= None) :
      '''
      Agrega una (lista de) secuencia(s) de bytes al contenido de memoria del
      tipo lineal. Se invoca de dos formas :
        addBytes(L[0:n]), donde L[i] tiene la forma [start_address, byte[0:m]]
      si n = 1, puede invocarse directamente :
        addBytes(start_address, byte[0:n])
      '''
      # [TO DO] Editar IntelHex.addULBAbytes()
      pass


   def addUSBAbytes(arg1, arg2= None) :
      '''
      Agrega una (lista de) secuencia(s) de bytes al contenido de memoria del
      tipo lineal. Se invoca de dos formas :
        addBytes(L[0:n]), donde L[i] tiene la forma [start_address, byte[0:m]]
      si n = 1, puede invocarse directamente :
        addBytes(start_address, byte[0:n])
      '''
      # [TO DO] Editar IntelHex.addUSBAbytes()
      pass


   def addRecords(self, records) :
      data_typ_parsing = None
      for rec in records :
         if rec.typ == 'data' :
            if data_typ_parsing == 'ulba' :
               self.ulba.add(rec)
            elif data_typ_parsing == 'usba' :
               self.usba.add(rec)
            else :
               ValueError('Error : Registro de datos (Data Record) sin asignación previa del tipo de memoria (i.e. sin un registro del tipo ULBA o USBA).')



         elif rec.typ == 'end_of_file' :
            # [TO DO] : Verificar que no existan mas registros.
            break

         elif rec.typ == 'ulba' :
            data_typ_parsing = 'ulba'
            self.ulba.base_adr = (rec.info[0]*256 + rec.info[1]) * 65536

         elif rec.typ == 'usba' :
            data_typ_parsing = 'usba'
            self.usba.base_adr = (rec.info[0]*256 + rec.info[1]) * 16

         elif rec.typ == 'csip' :
            if self.csip  == None :
               self.csip = rec
            else :
               ValueError('Error : Asignación CSIP duplicada.')

         elif rec.typ == 'eip' :
            if self.eip  == None :
               self.eip = rec
            else :
               ValueError('Error : Asignación EIP duplicada.')


   def __str__(self) :
      txt = ''
      # Codifica la memoria ULBA :
      if self.ulba.data != [] :
         base_adr = self.ulba.data[0].start & 0xFFFF0000
         txt += UlbaRecord(base_adr//65536).__str__() + '\n'

         for data_range in self.ulba.data :
            adr = data_range.start

            while adr < data_range.end :
               if (adr - base_adr) >= 0x10000 :
                  base_adr += adr & 0xFFFF0000
                  txt += UlbaRecord(base_adr//65536).__str__() + '\n'
                  continue

               length = min(16, data_range.end + 1 - adr, base_adr + 0x10000 - adr)
               txt += DataRecord(adr - base_adr, data_range.bytes[adr - data_range.start : ], length).__str__() + '\n'

               adr += length

      # Codifica la memoria USBA :
      if self.usba.data != [] :
         base_adr = self.ulba.data[0].start & 0xFFFFFFF0
         txt += UsbaRecord(base_adr//16).__str__() + '\n'

         for data_range in self.usba.data :
            adr = data_range.start
            while adr < data_range.end :
               if (adr - base_adr) >= 0x10000 :
                  base_adr += adr & 0xFFFFFFF0
                  txt += UlbaRecord(base_adr//16).__str__() + '\n'
                  continue

               length = min(16, data_range.end + 1 - adr, base_adr + 0x10000 - adr)
               txt += DataRecord(adr - base_adr, data_range[adr - data_range.start : ], length).__str__() + '\n'

               adr += length

      # Codifica la dirección de ejecución real (CSIP) :
      if self.csip is not None :
         txt += self.csip.__str__() + '\n'

      # Codifica la dirección de ejecución real (CSIP) :
      if self.eip is not None :
         txt += self.eip.__str__() + '\n'

      # Fin del registro
      txt += EndRecord().__str__() + '\n'

      return txt
