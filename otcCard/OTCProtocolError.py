#!/usr/bin/python
# -*- coding: utf-8 -*-

class OTCProtocolError(Exception):
  def __init__(self, msg, cause=None, obj=None) :
    super().__init__(self, msg)

    self.msg = msg

    if isinstance(cause, OTCProtocolError):
        self.msg += u'\nrazón : %s' % cause.msg

    elif isinstance(cause, Exception):
        self.msg += u'\nrazón : %s' % cause.args[0]

    elif cause :
        self.msg += u'\nrazón : %s' % cause.__str__()

    if obj: obj.log.error(msg)

    self.message = self.msg

