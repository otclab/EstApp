#!/usr/bin/python
# -*- coding: utf-8 -*-

# Versión 1.04
#   - Se reasigna el formato de punto flotante de Microchip de 'F' por 'M', y se asigna
#     el formato 'F' al de punto flotante IEE754
#
# Versión 1.03
#   - Se completa el soporte del formato 'F' correspondiente al formato utilizado por 
#     Microchip para los numeros en formato de punto flotante de 24 bis.
#
# Versión 1.02
#   - Se corrige la interpretación de los formatos 'g' y 'j' en el método '_unpack'.
  
import struct
import math

class ext_struct(object) :
  # Diccionario de las longitudes de cada tipo de formato :
  fmt_len = {'x':1, 'c':1, 'b':1, 'B':1, '?':1, 'h':2, 'H':2, 'i':4, 'I':4,
             'l':4, 'L':4, 'q':8, 'Q':8, 'f':4, 'F':3, 'M':3, 'd':8, 's':1,
             'g':3, 'G':3, 'J':5, 'j':5 }
             
  fmt_base = {'F' : 'L', 'M' : 'L', 'G': 'L', 'J' : 'Q'}

  @staticmethod
  def __pack(b_order, fmt, val) :
    if fmt in 'xcbB?hHiIlLqQnNefdspq' :
      return struct.pack(b_order + fmt, val)


    if fmt in ['g', 'j'] :
      if not isinstance(val, (int)) :
        raise ValueError('ext_struct : Los formatos g/G y j/J solo admiten argumentos instancias de int.')

      fmt = fmt.upper()
      
      if (val < 0) :
        val += 256**(fmt_len[fmt]) + val
        
      if (val < 0) or (val >= 2**(8*fmt_len[fmt] - 1)) :
        raise ValueError('argument out of range')
        
    if fmt in ['G', 'J'] : 
      if not isinstance(val, (int)) :
        raise ValueError('ext_struct : Los formatos g/G y j/J solo admiten argumentos instancias de int.')

      if  (val < 0) or (val >= 2**(8*fmt_len[fmt])) :
        raise ValueError('argument out of range')
        
      if b_order  == '>' :
        return struct.pack(b_order + fmt_base[fmt], val) #[fmt_len[fmt_base[fmt]] - fmt_len[fmt] : ]
       
      elif b_order == '<' :
        return struct.pack(b_order + fmt_base[fmt], val)[ : fmt_len[fmt] - fmt_len[fmt_base[fmt]]]
        
      else :
        raise ValueError('ext_struct : El orden de los bytes en los formato de números de 24 bits y 40 bits debe especificarse explicitamente.')

    if fmt == 'M' :
      """ Formato de 24 bits de Microchip :  
                  eeeeeeee sccccccc cccccccc
                  
          representa al número
                  N = ((s == 0)? 0 : 1) * (1 + c/32768) *2^(e - 127)        
          donde s, e y c representan :
             s el signo :  s = 1 if N<0 else 0 
             e el exponente sesgado  = floor(log2(|N|) + 127
             c el coeficiente        = round( |N|/2^(e-127) - 1 )
               
          El número cero se representa por 0x000000.  
      """
      if not isinstance(val, (int, float)) :
        raise ValueError("ext_struct : El formato 'F' admite numeros enteros o de punto flotante.")

      if (val < 2 **(-127) * 32767) or (val > 2**(128) * 32767) :
        raise ValueError('argument out of range')

      if val == 0 :
         exp, sig, coeff = (0,0,0)
      else :
        if val < 0  :
          sig = 1
          val = -val
        else :
          sig = 0

        exp = int(math.floor(math.log2(val))) + 127
        coeff = int((val/2**(exp - 127) - 1)*32768 + 0.5)

      return struct.pack('<I', exp*65536 + sig*32768 + coeff)[:3]
    
    if fmt == 'F' :
      """ Formato de 24 bits IEE754 :  
                  seeeeeee eccccccc cccccccc
                  
          representa al número
                  N = ((s == 0)? 0 : 1) * (1 + c/32768) *2^(e - 127)        
          donde s, e y c representan :
             s el signo :  s = 1 if N<0 else 0 
             e el exponente sesgado  = floor(log2(|N|) + 127
             c el coeficiente        = round( |N|/2^(e-127) - 1 )
               
          El número cero se representa por 0x000000.  
      """
      if not isinstance(val, (int, float)) :
        raise ValueError("ext_struct : El formato 'M' admite numeros enteros o de punto flotante.")

      if (val < 2 **(-127) * 32767) or (val > 2**(128) * 32767) :
        raise ValueError('argument out of range')

      if val == 0 :
         exp, sig, coeff = (0,0,0)
      else :
        if val < 0  :
          sig = 1
          val = -val
        else :
          sig = 0

        exp = int(math.floor(math.log2(val))) + 127
        coeff = int((val/2**(exp - 127) - 1)*32768 + 0.5)

      return struct.pack('<I', exp*32768 + sig*128*65536 + coeff)[:3]

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

    if fmt == 'M' :
      """ Formato de 24 bits de Microchip :  
                  eeeeeeee sccccccc cccccccc

          representa al número
                  N = ((s == 0)? 0 : 1) * (1 + c/32768) *2^(e - 127)        
          donde s, e y c representan :
             s el signo :  s = 1 if N<0 else 0 
             e el exponente sesgado  = floor(log2(|N|) + 127
             c el coeficiente        = round( |N|/2^(e-127) - 1 )

          El número cero se represnta po 0x000000.  
      """
      if b_order == '>' :
        tmp = packed_bytes[2]
        packed_bytes[2] = packed_bytes[0]
        packed_bytes[0] = tmp

      sig = 1 if packed_bytes[1] < 128 else -1
      exp = packed_bytes[2] - 127
      coeff = 1 + ((0x7F & packed_bytes[1])*256 +  packed_bytes[0])/32768
    
      val = (sig*coeff*2**(exp) ,)

      return val

    if fmt == 'F' :
      """ Formato de 24 bits IEE754 :  
                  seeeeeee eccccccc cccccccc
                  
          representa al número
                  N = ((s == 0)? 0 : 1) * (1 + c/32768) *2^(e - 127)        
          donde s, e y c representan :
             s el signo :  s = 1 if N<0 else 0 
             e el exponente sesgado  = floor(log2(|N|) + 127
             c el coeficiente        = round( |N|/2^(e-127) - 1 )
               
          El número cero se representa por 0x000000.  
      """
      if b_order == '>' :
        tmp = packed_bytes[2]
        packed_bytes[2] = packed_bytes[0]
        packed_bytes[0] = tmp

      sig = 1 if packed_bytes[2] < 128 else -1
      exp = (0x7F & packed_bytes[2])*2 + (1 if packed_bytes[1] > 127 else 0) - 127
      coeff = 1 + ((0x7F & packed_bytes[1])*256 +  packed_bytes[0])/32768
      
      val = (sig*coeff*2**(exp) ,)

      return val

    # Formatos g/G y j/J :
    val = struct.unpack(b_order + ext_struct.fmt_base[fmt.upper()], packed_bytes)

    if fmt in ['g', 'j'] :
      if val[0] >= 2**(8*ext_struct.fmt_len[fmt] - 1) :
        val = (val[0] - 256**(ext_struct.fmt_len[fmt]), )

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

