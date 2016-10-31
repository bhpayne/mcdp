# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import check_isinstance
from mcdp_posets import Map, Nat, RcompUnits, is_top
from mcdp_posets.nat import Nat_mult_uppersets_continuous
from mcdp_posets.rcomp import Rcomp_multiply_upper_topology


__all__ = [
    'MultValueNatMap', 
    'MultValueMap',
]

class MultValueNatMap(Map):

    @contract(value=int)
    def __init__(self, value):
        self.value = value
        self.N = Nat()
        Map.__init__(self, dom=self.N, cod=self.N)

    def _call(self, x):
        return Nat_mult_uppersets_continuous(self.value, x) 



class MultValueMap(Map):
    """ 
        Multiplies by <value>.
        Implements _ -> _ * x on RCompUnits with the upper topology
        constraint (⊤ * 0 = 0 * ⊤ = 0)
    """
    def __init__(self, F, R, unit, value):
        check_isinstance(unit, RcompUnits)
        check_isinstance(F, RcompUnits)
        check_isinstance(R, RcompUnits)
        dom = F
        cod = R
        self.value = value
        self.unit = unit
        Map.__init__(self, dom=dom, cod=cod)

    def diagram_label(self):
        from mcdp_posets.rcomp_units import format_pint_unit_short
        if is_top(self.unit, self.value):
            label = '× %s' % self.unit.format(self.value)
        else:
            assert isinstance(self.value, float)
            label = '× %.5f %s' % (self.value, format_pint_unit_short(self.unit.units))
        return label

    def _call(self, x):
        return Rcomp_multiply_upper_topology(self.dom, x, 
                                             self.unit, self.value, 
                                             self.cod)