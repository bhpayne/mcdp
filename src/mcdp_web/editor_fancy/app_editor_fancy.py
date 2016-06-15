
from contracts.utils import raise_wrapped
from mcdp_cli.plot import png_pdf_from_gg
from mcdp_report.gg_ndp import STYLE_GREENREDSYM, gvgen_from_ndp
from mcdp_report.html import ast_to_html
from mcdp_web.utils import (
    ajax_error_catch, format_exception_for_ajax_response, png_error_catch,
    response_data, response_image)
from mocdp.comp.composite import CompositeNamedDP
from mocdp.exceptions import DPSemanticError
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
import cgi
import os


class AppEditorFancy():

    def __init__(self):

        # model_name -> ndp
        self.last_processed = {}


    def config(self, config):

        config.add_route('edit_form_fancy', 
                         self.get_lmv_url('{library}', '{model_name}', 'edit_fancy'))
        config.add_view(self.view_edit_form_fancy, route_name='edit_form_fancy',
                        renderer='editor_fancy/edit_form_fancy.jinja2')

        config.add_route('ajax_parse', 
                         self.get_lmv_url('{library}', '{model_name}', 'edit_fancy') + 'ajax_parse')
        
        config.add_view(self.ajax_parse, route_name='ajax_parse',
                        renderer='json')

        config.add_route('editor_fancy_save',
                         self.get_lmv_url('{library}', '{model_name}', 'edit_fancy') + 'save')
        
        config.add_view(self.editor_fancy_save, route_name='editor_fancy_save',
                        renderer='json')

        config.add_route('new_model', '/libraries/{library}/new_model/{model_name}')
        config.add_view(self.view_new_model, route_name='new_model')

        config.add_route('graph', self.get_lmv_url('{library}', '{model_name}', 'edit_fancy') + 'graph.png')
        config.add_view(self.graph, route_name='graph')


    def editor_fancy_save(self, request):
        string = self.get_text_from_request(request)
        model_name = self.get_model_name(request)
        def go():
            l = self.get_library(request)
            l.write_to_model(model_name, string)
            return {'ok': True}

        return ajax_error_catch(go)

    def get_model_name(self, request):
        model_name = str(request.matchdict['model_name'])  # unicode
        return model_name

    def view_edit_form_fancy(self, request):
        model_name = self.get_model_name(request)
        filename = '%s.mcdp' % model_name
        l = self.get_library(request)
        f = l._get_file_data(filename)
        source_code = f['data']
        realpath = f['realpath']
        nrows = int(len(source_code.split('\n')) + 6)
        nrows = min(nrows, 25)

        source_code = cgi.escape(source_code)
        return {'source_code': source_code,
                'model_name': model_name,
                'realpath': realpath,
                'rows': nrows,
                'navigation': self.get_navigation_links(request),
                'error': None}

    def get_text_from_request(self, request):
        """ Gets the 'text' field, taking care of weird
            unicode characters from the browser. """
        string = request.json_body['text']
        # \xa0 is actually non-breaking space in Latin1 (ISO 8859-1), also chr(160).
        # You should replace it with a space.
        string = string.replace(u'\xa0', u' ')

        try:
            string = str(string.decode('utf-8'))
        except UnicodeEncodeError as e:

            string = string.encode('unicode_escape')
            raise_wrapped(Exception, e, 'What', in_ascii=string)

        return string
         
    def ajax_parse(self, request):
        model_name = self.get_model_name(request)
        string = self.get_text_from_request(request)
        req = {'text': request.json_body['text']}

        def go():
            try:
                highlight = ast_to_html(string,
                                    complete_document=False,
                                    add_line_gutter=False,
                                    encapsulate_in_precode=False, add_css=False)

                try:

                    l = self.get_library(request)
                    ndp = l.parse_ndp(string)

                except DPSemanticError as e:
                    self.last_processed[model_name] = None  # XXX
                    res = format_exception_for_ajax_response(e, quiet=(DPSemanticError,))
                    res['highlight'] = highlight
                    res['request'] = req
                    return res

                self.last_processed[model_name] = ndp
            except:
                self.last_processed[model_name] = None  # XXX

                raise

            return {'ok': True, 'highlight': highlight, 'request': req}

        return ajax_error_catch(go)

    def graph(self, request):
        def go():
            model_name = self.get_model_name(request)

            if not model_name in self.last_processed:
                l = self.get_library(request)
                ndp = l.load_ndp2(model_name)
            else:
                ndp = self.last_processed[model_name]
                if ndp is None:
                    return response_image(request, 'Could not parse model.')

            if isinstance(ndp, CompositeNamedDP):
                ndp2 = ndp.templatize_children()
                setattr(ndp2, '_hack_force_enclose', True)
            else:
                ndp2 = ndp
                setattr(ndp2, '_xxx_label', model_name)

            # ndp2 = cndp_get_suitable_for_drawing(model_name, ndp)

            gg = gvgen_from_ndp(ndp2, STYLE_GREENREDSYM, direction='TB')
            png, _pdf = png_pdf_from_gg(gg)
            return response_data(request=request, data=png, content_type='image/png')
        return png_error_catch(go, request)

    def view_new_model(self, request):
        library = self.get_current_library_name(request)
        model_name = str(request.matchdict['model_name'])  # unicode
        basename = model_name + '.mcdp'
        l = self.get_library(request)
        if l.file_exists(basename):
            error = 'File %r already exists.' % basename
            return render_to_response('editor_fancy/error_model_exists.jinja2',
                                      {'error': error,
                                       'url_edit': self.get_lmv_url(library, model_name, 'edit_fancy'),
                                       'model_name': model_name}, request=request)

        else:

            path = self.libraries[library]['path']
            source = "mcdp {\n\n}"
            filename = os.path.join(path, 'created', basename)

            d = os.path.dirname(filename)
            if not os.path.exists(d):
                os.makedirs(d)

            with open(filename, 'w') as f:
                f.write(source)
            l._update_file(filename)

            url = '/libraries/%s/models/%s/views/edit_fancy/' % (library, model_name)
            raise HTTPFound(url)


# def cndp_get_suitable_for_drawing(model_name, ndp):
#
#     ndp = ndp.templatize_children()
#
#     ONE = model_name
#     c = Context()
#
#     c.add_ndp(ONE, ndp)
#
#     for fname in ndp.get_fnames():
#         F = ndp.get_ftype(fname)
#         fn = c.add_ndp_fun_node(fname, F)
#
#         cc = Connection(dp1=fn, s1=fname, dp2=ONE, s2=fname)
#         c.add_connection(cc)
#
#     for rname in ndp.get_rnames():
#         R = ndp.get_rtype(rname)
#         rn = c.add_ndp_res_node(rname, R)
#
#         cc = Connection(dp1=ONE, s1=rname, dp2=rn, s2=rname)
#         c.add_connection(cc)
#
#     ndp2 = CompositeNamedDP.from_context(c)
#
#     return ndp2