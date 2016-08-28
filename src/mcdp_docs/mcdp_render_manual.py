# -*- coding: utf-8 -*-
from .manual_join_imp import manual_join
from mcdp_library import MCDPLibrary
from mcdp_library_tests.tests import get_test_librarian
from mcdp_report.gg_utils import embed_images_from_library
from mcdp_web.renderdoc.highlight import get_minimal_document
from mcdp_web.renderdoc.main import render_complete
from mocdp import logger
from quickapp import QuickApp
import logging
import os
import tempfile

manual_contents = [
    ('manual', 'tour'),
    ('manual', 'tour_intro'),
    ('manual', 'tour_composition'),
    ('manual', 'tour_catalogue'),
    ('manual', 'tour_coproduct'),
    ('manual', 'tour_templates'),
    ('manual', 'tour_uncertainty'),
    ('manual', 'scenarios'),
    ('droneD_complete_v2', 'drone_complete'),
    ('plugs', 'sockets'),
    ('plugs', 'sockets2'),
    ('actuation', 'actuation_tour'),
    ('rover_energetics', 'energy_choices'),
    ('rover_energetics', 'energy_choices2'),
    ('rover_energetics', 'energy_choices3'),
    ('manual', 'reference'),
    ('manual', 'types'),
    ('manual', 'types_scalar'),
    ('manual', 'types_finite_posets'),
    ('manual', 'types_poset_products'),
#     ('manual', 'adv_approximations'),
    ('manual', 'extra'),
]

class RenderManual(QuickApp):
    """ Evaluates one of the constants """

    def define_options(self, params):
        params.add_string('output_file', help='Output file')
        params.add_flag('cache')
        params.add_flag('pdf', help='Generate PDF version of code and figures.')

    def define_jobs_context(self, context):
        logger.setLevel(logging.DEBUG)

        options = self.get_options()
        out_dir = None

        if out_dir is None:
            out_dir = os.path.join('out', 'mcdp_render_manual')

        generate_pdf = options.pdf
        files_contents = []
        for libname, docname in manual_contents:
            res = context.comp(render, libname, docname, generate_pdf,
                               job_id='render-%s-%s' % (libname, docname))
            files_contents.append(res)

        d = context.comp(manual_join, files_contents)
        context.comp(write, d, options.output_file)

def write(s, out):
    with open(out, 'w') as f:
        f.write(s)
    print('Written %s ' % out)

def render(libname, docname, generate_pdf):
    librarian = get_test_librarian()
    library = librarian.load_library('manual')

    d = tempfile.mkdtemp()
    library.use_cache_dir(d)

    l = library.load_library(libname)
    basename = docname + '.' + MCDPLibrary.ext_doc_md
    f = l._get_file_data(basename)
    data = f['data']
    realpath = f['realpath']

    html_contents = render_complete(library=l,
                                    s=data, raise_errors=True, realpath=realpath,
                                    generate_pdf=generate_pdf)
    html_contents = embed_images_from_library(html=html_contents, library=l)

    doc = get_minimal_document(html_contents, add_markdown_css=True)
    return ((libname, docname), doc)
    

mcdp_render_manual_main = RenderManual.get_sys_main()
