#!/usr/bin/python
# -*- coding: utf-8 -*-

# Versión 1.02
#   - Se corrige la interpretación de los formatos 'g' y 'j' en el método '_unpack'.
  
import struct


class ext_struct(object) :
  # Diccionario de las longitudes de cada tipo de formato :
  fmt_len = {'x':1, 'c':1, 'b':1, 'B':1, '?':1, 'h':2, 'H':2, 'i':4, 'I':4,
             'l':4, 'L':4, 'q':8, 'Q':8, 'f':4, 'F':3, 'd':8, 's':1,
             'g':3, 'G':3, 'J':5, 'j':5 }
             
  fmt_base = {'G': 'L', 'J' : 'Q'}

  @staticmethod
  def __pack(b_order, fmt, val) :
    if fmt in 'xcbB?hHiIlLqQnNefdspq' :
      return struct.pack(b_order + fmt, val)

    if not isinstance(val, (int)) :
      raise('ext_struct : Los formatos g/G y j/J solo admiten argumentos instancias de int.')
      
    if fmt in ['g', 'j'] :
      fmt = fmt.upper()
      
      if (val < 0) :
        val += 256**(fmt_len[fmt]) + val
        
      if (val < 0) or (val >= 2**(8*fmt_len[fmt] - 1)) :
        raise ValueError('argument out of range')
        
    if fmt in ['G', 'J'] : 
      if  (val < 0) or (val >= 2**(8*fmt_len[fmt])) :
        raise ValueError('argument out of range')
        
      if b_order  == '>' :
        return struct.pack(b_order + fmt_base[fmt], val) #[fmt_len[fmt_base[fmt]] - fmt_len[fmt] : ]
       
      elif b_order == '<' :
        return struct.pack(b_order + fmt_base[fmt], val)[ : fmt_len[fmt] - fmt_len[fmt_base[fmt]]]
        
      else :
        raise ValueError('ext_struct : El orden de los bytes en los formato de números de 24 bits y 40 bits debe especificarse explicitamente.')
     
     
    raise ValueError('ext_struct : El formato no es reconocido.')     

   
  @staticmethod
  def pack(fmt, *val) :
    # Se asegura que val sea una tupla :
    if not isinstance(val, tuple) : val = (val,)

    # Se reconoce el orden de la conversión a bytes :
    if fmt[0] in ['<', '>', '!', '@', '!'] :
      _fmt = fmt[1:]
      f0   = fmt[0]
    else :
      _fmt = fmt
      f0   = ''

    pack_bytes = b''
    
    while _fmt :
      multiplier = ''
      while _fmt[0] in '0123456789' :
        multiplier += _fmt[0]
        _fmt = _fmt[1:]

      if not multiplier:
        multiplier = '1'

      if not (_fmt[0] in 'xcbB?hHiIlLqQnNefdspqgGjJ') :
        ValueError('ext_struct : El formato no es reconocido.')

      if _fmt[0] in 'sp' :
        pack_bytes += struct.pack(f0 + multiplier + _fmt[0], val[0].encode('utf-8'))
        val = val[1:]
      else :
        for n in range(int(multiplier)) :
          pack_bytes += ext_struct.__pack(f0, _fmt[0], val[0])
          val = val[1:]

      _fmt = _fmt[1:]

    return pack_bytes
    
    
  @staticmethod
  def __unpack(b_order, fmt, packed_bytes) :
    if fmt in 'xcbB?hHiIlLqQnNefdspq' :
      return struct.unpack(b_order + fmt, packed_bytes)
      
    if b_order == '>' :
      packed_bytes =  (ext_struct.fmt_len[ext_struct.fmt_base[fmt.upper()]] - ext_struct.fmt_len[fmt])*b'\x00' + packed_bytes 
    elif b_order == '<' :
      packed_bytes +=  (ext_struct.fmt_len[ext_struct.fmt_base[fmt.upper()]] - ext_struct.fmt_len[fmt])*b'\x00'
    else :
      raise ValueError('ext_struct : El orden de los bytes en los formato de números de 24 bits y 40 bits debe especificarse explicitamente.')
    
    val = struct.unpack(b_order + ext_struct.fmt_base[fmt.upper()], packed_bytes)

    if fmt in ['g', 'j'] :
      val = val[0]
      if val >= 2**(8*ext_struct.fmt_len[fmt] - 1) :
        val -= 256**(ext_struct.fmt_len[fmt])
        
      if (val < 0) or (val >= 2**(8*ext_struct.fmt_len[fmt] - 1)) :
        raise ValueError('argument out of range')

      val = (val,)
      
    return val
       
  
  @staticmethod
  def unpack(fmt, packed_bytes) :
    strip =  lambda x : strip(x[:-1]) if x[-1] in [0, ord(' ')] else x.decode('ansi')
    
    # Se reconoce el orden de la conversión a bytes :
    if fmt[0] in ['<', '>', '!', '@', '!'] :
      _fmt = fmt[1:]
      f0   = fmt[0]
    else : 
      _fmt = fmt
      f0   = ''

    val = []
    
    while _fmt :
      multiplier = ''
      while _fmt[0] in '0123456789' :
        multiplier += _fmt[0]
        _fmt = _fmt[1:]

      if not multiplier :
        multiplier = '1'

      if not (_fmt[0] in 'xcbB?hHiIlLqQnNefdspqgGjJ') :
        ValueError('ext_struct : El formato no es reconocido.')

      if _fmt[0] in 'sp':
        field = []

        for n in range(int(multiplier)) :
          field.append( ext_struct.__unpack(f0, _fmt[0], packed_bytes[:ext_struct.fmt_len[_fmt[0]]])[0] )
          packed_bytes = packed_bytes[ext_struct.fmt_len[_fmt[0]]:]
         
        val.append(strip(b''.join(field)))

      else :
        for n in range(int(multiplier)) :
          val.append( ext_struct.__unpack(f0, _fmt[0], packed_bytes[:ext_struct.fmt_len[_fmt[0]]])[0] )
          packed_bytes = packed_bytes[ext_struct.fmt_len[_fmt[0]]:]

      _fmt = _fmt[1:]

    return tuple(val)


  @staticmethod
  def calcsize(fmt) :
    if fmt[0] in ['<', '>', '!', '@', '!'] :
      _fmt = fmt[1:]
    else :
      _fmt = fmt

    c_size = 0
    
    while _fmt :
      multiplier = ''
      while _fmt[0] in '0123456789' :
        multiplier += _fmt[0]
        _fmt = _fmt[1:]

      if not (_fmt[0] in 'xcbB?hHiIlLqQnNefdspqgGjJ') :
        ValueError('ext_struct : El formato no es reconocido.')
        
      if multiplier == '' :
        multiplier = 1 
      else :
        multiplier = int(multiplier)
        
      c_size += multiplier*ext_struct.fmt_len[_fmt[0]]
      _fmt = _fmt[1:]
      
    return c_size




  
  
#  @staticmethod
#  def pack(fmt, *val) :
#    # Se asegura que val sea una tupla :
#    if not isinstance(val, tuple) : val = (val,)
#
#    # Se reconoce el orden de la conversión a bytes :
#    if fmt[0] in ['<', '>'] :
#      _fmt = fmt[1:]
#      f0   = fmt[0]
#    else :
#      _fmt = fmt
#      f0   = ''
#
#    # Se procesas los formatos 'g' y 'G' (entero de 24 bits).
#
#    # Se utiliza el formato I eliminando el primer o último byte dependiendo
#    # del ordenamiento :
#    if f0 == '>' :
#      g_bytes = lambda x : tuple([s for s in struct.pack(f0+'I', x)[1:]])
#    else :
#      g_bytes = lambda x : tuple([s for s in struct.pack(f0+'I', x)[:-1]])
#
#    # El procedimiento consiste en reemplazar las apariciones de 'g' y 'G'
#    # por 'ccc' en el formato y por su descomposición en bytes en val :
#    end = len(_fmt)
#    while (1):
#      # El reemplazo se realiza desde la derecha hacia la izquierda, ya que de
#      # esta forma los índices de las siguientes reemplazos :
#      end = max(_fmt.rfind('g', 0, end), _fmt.rfind('G', 0, end))
#
#      if end < 0 : break
#
#      # Si se utiliza el formato con signo, se convierte a su complemento a 2 :
#      _val = val[end]
#      if (_fmt[end] == 'g') and (val[end] <  0) :
#          _val = 2**24 + val[end]
#
#      val = val[:end] + g_bytes(_val) + val[end+1:]
#      _fmt = _fmt[:end] + 'ccc' + _fmt[end+1:]
#
#    # se procesa el formato F (coma flotante de 24 bits).
#
#    # Se utiliza el formato L eliminando el primer o último byte dependiendo
#    # del ordenamiento :
#    if f0 == '>' :
#      F_bytes = lambda x : tuple([s for s in struct.pack(f0+'L', x)[:-1]])
#    else :
#      F_bytes = lambda x : tuple([s for s in struct.pack(f0+'L', x)[1:]])
#
#    # El procedimiento consiste en reemplazar las apariciones de 'F' por
#    # por 'ccc' en el formato y por su descomposición en bytes en val :
#    end = len(_fmt)
#    while (1):
#      end = _fmt.rfind('F', 0, end)
#
#      if end < 0 : break
#
#      val = val[:end] + F_bytes(val[end]) + val[end+1:]
#      _fmt = _fmt[:end] + 'ccc' + _fmt[end+1:]
#
#    # Finalmente se puede utilizar la función de empaquetado estándar de struct:
#    return struct.pack(f0 + _fmt, *val)
#
#
#  @staticmethod
#  def unpack(fmt, str) :
#    # Se reconoce el ordenamiento :
#    if fmt[0] in ['<', '>'] :
#      fmt = fmt[1:]
#      f0  = fmt[0]
#    else :
#      f0  = ''
#
#    # Los formatos (adicionales) de 24 bits se reemplazan por 'ccc' :
#    _fmt = fmt.replace('g', 'ccc')
#    _fmt = _fmt.replace('G', 'ccc')
#    _fmt = _fmt.replace('F', 'ccc')
#
#    val = struct.unpack('<'+_fmt, str) # list(struct.unpack(_fmt, str))
#    start = 0
#    while (1) :
#      idx = [n for n in [fmt.find('g', start), fmt.find('G', start), fmt.find('F', start)] if n >= 0]
#
#      if idx == [] : break ;
#      start = min(idx)
#
#      if start is None : break
#
#      val_chr = val[start:start+3]
#
#      if f0 == '>' : val_chr.reverse()
#
#      if fmt[start] == 'g' :
#        if ord(val_chr[2]) > 127 :
#         _val = struct.unpack('<i', ''.join(val_chr) + '\xFF')
#        else :
#         _val = struct.unpack('<i', ''.join(val_chr) + '\x00')
#
#      elif fmt[start] == 'G' :
#        _val = struct.unpack('<I', ''.join(val_chr) + '\x00')
#
#      else : # solo puede ser _fmt[start] == 'F'
#        _val = struct.unpack('<f', '\x00' + ''.join(val_chr))
#
#      val = val[:start] + _val + val[start+3:]
#      start +=1
#
#    return tuple(val)
#
#
#  @staticmethod
#  def calcsize(fmt) :
#    _fmt = fmt.replace('g', 'ccc')
#    _fmt = _fmt.replace('G', 'ccc')
#    _fmt = _fmt.replace('F', 'ccc')
#
#    return struct.calcsize(_fmt)

