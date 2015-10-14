# -*- coding: utf-8 -*-
from .primitive import PrimitiveDP
from mocdp import get_conftools_posets
from mocdp.posets import PosetProduct
from mocdp.posets.uppersets import UpperSet


__all__ = [
    'Terminator',
]

class Terminator(PrimitiveDP):
    """ Terminates a signal line """

    def __init__(self, F):
        library = get_conftools_posets()
        _, F = library.instance_smarter(F)

        R = PosetProduct(())

        PrimitiveDP.__init__(self, F=F, R=R)

    def solve(self, func):  # @UnusedVariable
        return UpperSet([()], self.R)

    def __repr__(self):
        return 'Term(%r)' % self.F
