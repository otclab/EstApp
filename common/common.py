#!/usr/bin/python
# -*- coding: utf-8 -*-

from otcCard import *
from estCard.EstCard import *



def openCard(port, throughput_limit = False, report = True) :
    """
    Inicia la conexión con la tarjeta conectada al puerto port, lee la identifi-
    ción de la tarjeta y devuelve un objeto de la clase EstCard.
    Si la tarjeta no es reconocida interroga al usuario se se continua o no.
    Por defecto presenta la identificación de la tarjeta en la consola, acción
    que es controlada por report.
    """
    try :
        print("Conectando ...", end='\r')
        card = EstCard(port, throughput_limit)

        if report :
            print("Conectado a :")
            print("      Hardware : %s" %card.id['hardware_model'   ])
            print("       Versión : %s" %card.id['hardware_version' ])
            print("      Software : %s" %card.id['software_kernel'  ])
            print("       versión : %s" %card.id['software_release' ])
            print("      revisión : %s" %card.id['software_revision'])
            print("\n")

        if not card.isKnown :
            ans = input('El modelo es desconocido!, ¿Se Continua? [S/N] ')

            if ans.lower() in ['n', 'no'] :
                sys.exit(0)

        return card

    except OTCProtocolError :
        sys.exit(1)


# Reconoce la especificación del puerto serie en la línea de comandos args como:
#  En el primer argumento como '-COMx', donde x es el número del puerto.
#  Como la opción que sigue a '-port'
#
# Si no se encuentra la especificación y la opción principal se encuentra en el
# argumento 'required', se interroga al usuario para que seleccione el puerto,
# de la lista puertos disponibles en el sistema,
def parsePort(args, required = []) :
    """
    Reconoce la especificación del puerto en args (importado de sys.args), de-
    vuelve una tupla cuyo primer elemento es el nombre del puerto y el segundo
    la lista args con la especificación del puerto removida.

    Si no encuentra la especificación del puerto, y args contiene la especifica-
    ción de una orden en la que es obligatorio especificarla, presenta una lista
    de los puertos disponibles y solicita la elección del usuario.

    La lista de ordenes en la que es obligatoria la especificación del puerto se
    importa por medio del parámetro required.

    Si la especificación del puerto no es requerida (y no se especifica en la
    linea de ordenes args) se le asigna None al devolverlo.
    """
    try :
        if args[1][0:4] == u'-COM' :
            port = args.pop(1)[1:]
        else :
            i = args.index(u'-port')
            args.pop(i)
            port = args.pop(i).upper()

        return (port, args)

    except :
        pass

    if (len(args) < 2) or (not args[1] in required) :
        return (None, args)

    ports = com_list()

    if len(ports) == 0 :
        print('Error : El Sistema no tiene puertos serie.')
        sys.exit()

    if len(ports) == 1 :
        print('Seleccionando el único puerto serie : {:s}'.format(ports[list(ports)[0]]))
        return (ports[list(ports)[0]], args)

    def porttype(p) :
        types = {'com0com' : 'Emulador Com0Com',
                'USBSER' : 'Adaptador USB' , 'BthModem': 'Adaptador Bluetooth'}
        for t in types.keys() :
            if p.startswith(t) : return types[t]
        return p

    print('Seleccione el puerto serie :')

    print('\n'.join(['   [%d] -> %-8s / %s'%
                (i+1, ports[k], porttype(k.split('\\')[-1]))
                                      for i,k in enumerate(ports.keys())]))

    while True :
        try :
            ans = input('\nIndice del puerto serie ? ')
            ans = int(ans)
            if (ans >= 0) and (ans < len(ports)) :
                break
        except :
            pass

        if ans in ['x', 'X'] :
            print('Operación abortada a petición')
            sys.exit(1)

        print('No es una selección válida. Intente de nuevo.')
        print('x si desea salir.')

    return (ports[list(ports.keys())[ans]], args)

