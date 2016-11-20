# -*- coding: utf-8 -*-
from mcdp_report.dp_graph_flow_imp import dp_graph_flow
from mcdp_report.gg_ndp import gvgen_from_ndp
from mcdp_report.gg_utils import gg_get_format
from mcdp_web.utils.response import response_data
from mocdp.comp.composite_templatize import ndp_templatize
from mocdp.comp.template_for_nameddp import TemplateForNamedDP
from mocdp.exceptions import mcdp_dev_warning
from mcdp_figures.figure_interface import MakeFiguresNDP


class WebAppImages():

    def __init__(self):
        pass

    def config(self, config):
        config.add_route('solver_image',
                         '/libraries/{library}/models/{model_name}/views/solver/compact_graph.png')
        config.add_view(self.view_ndp_graph_templatized, route_name='solver_image')
        config.add_route('solver_image2',
                         '/libraries/{library}/models/{model_name}/views/solver/{fun_axes}/{res_axes}/compact_graph.png')
        config.add_view(self.view_ndp_graph_templatized, route_name='solver_image2')

        config.add_route('solver2_image',
                         '/libraries/{library}/models/{model_name}/views/solver2/compact_graph.png')
        config.add_view(self.view_ndp_graph_templatized, route_name='solver2_image')

        config.add_route('model_ndp_graph_image',
                         self.get_lmv_url('{library}', '{model_name}', 'ndp_graph') +
                         'image/{style}.{format}')
        config.add_view(self.view_model_ndp_graph_image, route_name='model_ndp_graph_image')

        config.add_route('model_dp_graph_image',
                         self.get_lmv_url('{library}', '{model_name}', 'dp_graph') +
                         'image/default.{format}')
        config.add_view(self.view_model_dp_graph_image, route_name='model_dp_graph_image')

        mf = MakeFiguresNDP(None)
        for x in mf.available(): 
            route_name = 'make_figures_%s' % x
            url = self.get_lmv_url('{library}', '{model_name}', 'images') + '{which}.{format}'
            config.add_route(route_name, url)
            config.add_view(self.make_figures, route_name=route_name)
        
        route_name = 'list_views'
        url = self.get_lmv_url('{library}', '{model_name}', 'images')
        config.add_route(route_name, url)
        config.add_view(self.list_views, route_name=route_name, renderer='images/list_views.jinja2')

    def make_figures(self, request):    
        l = self.get_library(request)
        id_ndp = self.get_model_name(request)
        context = l._generate_context_with_hooks()
        ndp = l.load_ndp(id_ndp, context)

        mf = MakeFiguresNDP(ndp=ndp, library=l, yourname=id_ndp)
        
        which = str(request.matchdict['which'])
        data_format = str(request.matchdict['format'])
        data = mf.get_figure(which, data_format)
        mime = get_mime_for_format(data_format)
        return response_data(request=request, data=data, content_type=mime)
 
    def list_views(self, request):
        available = []
        mf = MakeFiguresNDP(None)
        for x in sorted(mf.available()): 
            data_formats = mf.available_formats(x)
            available.append((x, data_formats))
        return {
            'available': available,
             'navigation': self.get_navigation_links(request),
            }
        
    # TODO: catch errors when generating images
    def view_ndp_graph_templatized(self, request):
        """ Returns an image """

        def go():
            l = self.get_library(request)
            id_ndp = self.get_model_name(request)
            context = l._generate_context_with_hooks()
            ndp = l.load_ndp(id_ndp, context)

            model_name = self.get_model_name(request)
            png = ndp_graph_templatized(library=l, ndp=ndp,
                                        yourname=model_name, data_format='png')

            return response_data(request=request, data=png, content_type='image/png')

        return self.png_error_catch2(request, go)

    def view_model_dp_graph_image(self, request):
        def go():
            id_ndp = self.get_model_name(request)
            fileformat = request.matchdict['format']
            library = self.get_library(request)

            context = library._generate_context_with_hooks()
            ndp = library.load_ndp(id_ndp, context)
            dp = ndp.get_dp()
            gg = dp_graph_flow(dp, direction='TB')

            data = gg_get_format(gg, fileformat)
            mime = get_mime_for_format(fileformat)
            return response_data(request=request, data=data, content_type=mime)

        return self.png_error_catch2(request, go)

    def view_model_ndp_graph_image(self, request):
        def go():
            id_ndp = self.get_model_name(request)
            style = request.matchdict['style']
            fileformat = request.matchdict['format']

            library = self.get_library(request)
            context = library._generate_context_with_hooks()
            ndp = library.load_ndp(id_ndp, context)

            data = ndp_graph_normal(library=library, ndp=ndp, style=style,
                                    yourname=id_ndp,
                                    data_format=fileformat)
            return response_data(request, data, get_mime_for_format(fileformat))

        return self.png_error_catch2(request, go) 

def get_mime_for_format(data_format):
    table = get_mime_table()
    return table[data_format]

def get_mime_table():
    d = {
         'pdf': 'image/pdf',
         'png': 'image/png',
         'jpg': 'image/jpg',
         'dot': 'text/plain',
         'txt': 'text/plain',
         'svg': 'image/svg+xml',
    }
    return d

def ndp_graph_templatized(library, ndp, yourname=None, data_format='png', direction='LR'):
    ndp = ndp_templatize(ndp, mark_as_template=False)
    images_paths = library.get_images_paths()
    from mcdp_report.gdc import STYLE_GREENREDSYM

    gg = gvgen_from_ndp(ndp, STYLE_GREENREDSYM, yourname=yourname,
                        images_paths=images_paths, direction=direction)
    return gg_get_format(gg, data_format)
    
def ndp_graph_normal(library, ndp, style, yourname, data_format, direction='LR'):
    """ This is not enclosed """
    images_paths = library.get_images_paths()
    gg = gvgen_from_ndp(ndp, style, images_paths=images_paths,
                        yourname=yourname, direction=direction)
    return gg_get_format(gg, data_format)

# 
# def ndp_graph_enclosed(library, ndp, style, yourname, data_format, direction='TB',
#                        enclosed=True):
#     """ This templatizes the children. It forces the enclosure if enclosure is True. """
#     from mocdp.comp.composite import CompositeNamedDP
#     from mocdp.ndp.named_coproduct import NamedDPCoproduct
#     from mocdp.comp.composite_templatize import cndp_templatize_children
#     from mocdp.comp.composite_templatize import ndpcoproduct_templatize
#     if isinstance(ndp, CompositeNamedDP):
#         ndp2 = cndp_templatize_children(ndp)
#         # print('setting _hack_force_enclose %r' % enclosed)
#         if enclosed:
#             setattr(ndp2, '_hack_force_enclose', enclosed)
#     elif isinstance(ndp, NamedDPCoproduct):
#         ndp2 = ndpcoproduct_templatize(ndp)
#     else:
#         ndp2 = ndp
# 
#     images_paths = library.get_images_paths()
#     # we actually don't want the name on top
#     yourname = None  # name
#     gg = gvgen_from_ndp(ndp2, style, direction=direction,
#                         images_paths=images_paths, yourname=yourname)
#     return gg_get_format(gg, data_format)

def ndp_template_enclosed(library, name, x, data_format):
    from mcdp_report.gdc import STYLE_GREENREDSYM

    return ndp_template_graph_enclosed(library, x, style=STYLE_GREENREDSYM, yourname=name,
                                       data_format=data_format, direction='TB', enclosed=True)

def ndp_template_graph_enclosed(library, template, style, yourname, data_format, direction, enclosed):
    assert isinstance(template, TemplateForNamedDP)
    mcdp_dev_warning('Wrong - need assume ndp const')

    context = library._generate_context_with_hooks()

    ndp = template.get_template_with_holes(context)

    if enclosed:
        setattr(ndp, '_hack_force_enclose', True)

    images_paths = library.get_images_paths()
    gg = gvgen_from_ndp(ndp, style=style, direction=direction,
                        images_paths=images_paths, yourname=yourname)
    return gg_get_format(gg, data_format)

# 
# def ndp_graph_expand(library, ndp, style, yourname, data_format, direction='TB'):
#     """ This expands the children, forces the enclosure """
#     mcdp_dev_warning('Wrong - need assume ndp const')
#     setattr(ndp, '_hack_force_enclose', True) 
# 
#     images_paths = library.get_images_paths()
#     # we actually don't want the name on top
#     yourname = None  # name
#     gg = gvgen_from_ndp(ndp, style, direction=direction,
#                         images_paths=images_paths, yourname=yourname)
# 
#     return gg_get_format(gg, data_format)

