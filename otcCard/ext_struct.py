#!/usr/bin/python
# -*- coding: utf-8 -*-


import struct


class ext_struct(object) :
  # Diccionario de las longitudes de cada tipo de formato :
  fmt_len = {'x':1, 'c':1, 'b':1, 'B':1, '?':1, 'h':2, 'H':2, 'i':4, 'I':4,
             'l':4, 'L':4, 'q':8, 'Q':8, 'f':4, 'F':3, 'd':8, 's':1,
             'g':3, 'G':3}

  @staticmethod
  def pack(fmt, *val) :
    # Se asegura que val sea una tupla :
    if not isinstance(val, tuple) : val = (val,)

    # Se reconoce el orden de la conversión a bytes :
    if fmt[0] in ['<', '>'] :
      _fmt = fmt[1:]
      f0   = fmt[0]
    else :
      _fmt = fmt
      f0   = ''

    # Se procesas los formatos 'g' y 'G' (entero de 24 bits).

    # Se utiliza el formato I eliminando el primer o último byte dependiendo
    # del ordenamiento :
    if f0 == '>' :
      g_bytes = lambda x : tuple([s for s in struct.pack(f0+'I', x)[1:]])
    else :
      g_bytes = lambda x : tuple([s for s in struct.pack(f0+'I', x)[:-1]])

    # El procedimiento consiste en reemplazar las apariciones de 'g' y 'G'
    # por 'ccc' en el formato y por su descomposición en bytes en val :
    end = len(_fmt)
    while (1):
      # El reemplazo se realiza desde la derecha hacia la izquierda, ya que de
      # esta forma los indíces de las siguientes reemplazos :
      end = max(_fmt.rfind('g', 0, end), _fmt.rfind('G', 0, end))

      if end < 0 : break

      # Si se utiliza el formato con signo, se convierte a su complemento a 2 :
      _val = val[end]
      if (_fmt[end] == 'g') and (val[end] <  0) :
          _val = 2**24 + val[end]

      val = val[:end] + g_bytes(_val) + val[end+1:]
      _fmt = _fmt[:end] + 'ccc' + _fmt[end+1:]

    # se procesa el formato F (coma flotante de 24 bits).

    # Se utiliza el formato f eliminando el primer o último byte dependiendo
    # del ordenamiento :
    if f0 == '>' :
      F_bytes = lambda x : tuple([s for s in struct.pack(f0+'f', x)[:-1]])
    else :
      F_bytes = lambda x : tuple([s for s in struct.pack(f0+'f', x)[1:]])

    # El procedimiento consiste en reemplazar las apariciones de 'F' por
    # por 'ccc' en el formato y por su descomposición en bytes en val :
    end = len(_fmt)
    while (1):
      end = _fmt.rfind('F', 0, end)

      if end < 0 : break

      val = val[:end] + F_bytes(val[end]) + val[end+1:]
      _fmt = _fmt[:end] + 'ccc' + _fmt[end+1:]

    # Finalmente se puede utilizar la función de empaquetado estándar de struct:
    return struct.pack(f0 + _fmt, *val)


  @staticmethod
  def unpack(fmt, str) :
    # Se reconoce el ordenamiento :
    if fmt[0] in ['<', '>'] :
      fmt = fmt[1:]
      f0  = fmt[0]
    else :
      f0  = ''

    # Los formatos (adicionales) de 24 bits se reemplazan por 'ccc' :
    _fmt = fmt.replace('g', 'ccc')
    _fmt = _fmt.replace('G', 'ccc')
    _fmt = _fmt.replace('F', 'ccc')

    val = struct.unpack('<'+_fmt, str) # list(struct.unpack(_fmt, str))
    start = 0
    while (1) :
      idx = [n for n in [fmt.find('g', start), fmt.find('G', start), fmt.find('F', start)] if n >= 0]

      if idx == [] : break ;
      start = min(idx)

      if start is None : break

      val_chr = val[start:start+3]

      if f0 == '>' : val_chr.reverse()

      if fmt[start] == 'g' :
        if ord(val_chr[2]) > 127 :
         _val = struct.unpack('<i', ''.join(val_chr) + '\xFF')
        else :
         _val = struct.unpack('<i', ''.join(val_chr) + '\x00')

      elif fmt[start] == 'G' :
        _val = struct.unpack('<I', ''.join(val_chr) + '\x00')

      else : # solo puede ser _fmt[start] == 'F'
        _val = struct.unpack('<f', '\x00' + ''.join(val_chr))

      val = val[:start] + _val + val[start+3:]
      start +=1

    return tuple(val)


  @staticmethod
  def calcsize(fmt) :
    _fmt = fmt.replace('g', 'ccc')
    _fmt = _fmt.replace('G', 'ccc')
    _fmt = _fmt.replace('F', 'ccc')

    return struct.calcsize(_fmt)

