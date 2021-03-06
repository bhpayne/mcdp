# -*- coding: utf-8 -*-
from contracts import contract
from mcdp_posets import UpperSet
from mcdp_posets.rcomp import finfo
from mcdp import logger
from mcdp.exceptions import mcdp_dev_warning
import numpy as np 

from .axis_algebra import enlarge_x, enlarge_y


@contract(us=UpperSet)
def plot_upset_R2(pylab, us, axis, color_shadow,
                  extra_space_shadow=0.05, color_lines='none', markers='r.',
                  marker_params={}):

    points = us.minimals

    xmin, xmax, ymin, ymax = axis
    for p in points:
        if xmin <= p[0] <= xmax and (ymin <= p[1] <= ymax):
            mcdp_dev_warning('This should be smarter')

            # draw a little of them
            if p[0] == xmax:
                axis = enlarge_x(axis, extra_space_shadow)
            if p[1] == ymax:
                axis = enlarge_y(axis, extra_space_shadow)

            plot_cone(pylab, p, axis, color_shadow=color_shadow,
                      color_lines=color_lines)
        else:
            logger.debug('Warning: point %s not in axis %s' % (p, axis))
            
    # cuteness
    if markers is not None:
        for p in points:
            # This is to avoid underflow
            # when using "finfo.tiny"
            eps = finfo.eps
            p = np.maximum(p, eps)
            #print('plot_upset_R2: marker params: %s ' % marker_params)
            pylab.plot(p[0], p[1], markers, clip_on=False, **marker_params)


def plot_cone(pylab, p, axis, color_shadow, color_lines):
    # This is to avoid underflow
    # when using "finfo.tiny"
    eps = finfo.eps
    p = np.maximum(p, eps)

    from matplotlib import patches
    [_, xmax, _, ymax] = axis


    ax1 = pylab.gca()
    ax1.add_patch(
    patches.Rectangle(
        p,  # (x,y)
        xmax - p[0],  # width
        ymax - p[1],  # height
        facecolor=color_shadow,
        edgecolor='none',
    ))

    pylab.plot([p[0], p[0]], [p[1], ymax], '-', color=color_lines)
    pylab.plot([p[0], xmax], [p[1], p[1]], '-', color=color_lines)






