# -*- coding: utf-8 -*-

# Copyright (C) 2017, Maximilian Köhl <mail@koehlma.de>

import ctypes
import ctypes.util
import os
import os.path
import typing


_libpicosat = ctypes.util.find_library('libpicosat')
if _libpicosat is None:
    _libpicosat = os.environ.get('LIBPICOSAT', None)
if _libpicosat is None:
    _libpicosat = os.path.join(os.path.dirname(__file__), 'libpicosat.so')

_library = ctypes.CDLL(_libpicosat)

_picosat_init = _library.picosat_init
_picosat_init.restype = ctypes.c_void_p

_picosat_reset = _library.picosat_reset
_picosat_reset.argtypes = [ctypes.c_void_p]

_picosat_add = _library.picosat_add
_picosat_add.argtypes = [ctypes.c_void_p, ctypes.c_int]

_picosat_assume = _library.picosat_assume
_picosat_assume.argtypes = [ctypes.c_void_p, ctypes.c_int]

_picosat_sat = _library.picosat_sat
_picosat_sat.argtypes = [ctypes.c_void_p, ctypes.c_int]
_picosat_sat.restype = ctypes.c_int

_picosat_deref = _library.picosat_deref
_picosat_deref.argtypes = [ctypes.c_void_p, ctypes.c_int]
_picosat_deref.restype = ctypes.c_int

_PICOSAT_SATISFIABLE = 10


class Solver:
    def __init__(self):
        self.sat = _picosat_init()
        self._has_solution = False

    def __del__(self):
        _picosat_reset(self.sat)

    def add_clause(self, literals: typing.Iterable[int]):
        for literal in literals:
            _picosat_add(self.sat, literal)
        _picosat_add(self.sat, 0)

    def add_assumption(self, literal):
        _picosat_assume(self.sat, literal)

    def get_solution(self, literal):
        assert self._has_solution
        return _picosat_deref(self.sat, literal) == 1

    def is_satisfiable(self, limit=-1):
        self._has_solution = _picosat_sat(self.sat, limit) == _PICOSAT_SATISFIABLE
        return self._has_solution
