# -*- coding: utf-8 -*-
from comptests.registrar import comptest
from mcdp_lang.syntax import Syntax
from .utils import parse_wrap_check


@comptest
def check_templates1():
    
    print parse_wrap_check('specialize [b1: `s1, b2: `s2] `sum_battery  ',
                    Syntax.ndpt_specialize)
    print parse_wrap_check('specialize [] `sum_battery',
                     Syntax.ndpt_specialize)


@comptest
def check_templates2():
    pass


@comptest
def check_templates3():
    pass


@comptest
def check_templates4():
    pass


@comptest
def check_templates5():
    pass
