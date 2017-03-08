import numpy as np

__all__ = ['MCDPConstants']


class MCDPConstants():
    """ Some system-wide constants """
    
    # source
    
    # preferred indent
    indent = 4
    # number of spaces to which a tab is equivalent
    tabsize = 4 
        
    
    #
    # Compilation stage
    #
    
    # only compile to graphs using two-factor multiplication for functions
    force_mult_two_functions = True
    # only compile to graphs using two-factor multiplication for resources
    force_mult_two_resources = True
    
    force_plus_two_resources = True
    
    # force_plus_two_functions = True # currently unused (InvPlus2 -> InvPlusN)
    
    # TODO: make algo configurable for invplus, etc. see also: InvMult2.ARGO 
    
    #
    # Testing
    #
    
    Nat_chain_include_maxint = False
    Rcomp_chain_include_tiny = False
    Rcomp_chain_include_eps = False
    Rcomp_chain_include_max = False
    
    # test the correspondence between h and h* (currently failing)
    test_dual01_chain = False
    
    # Ignore graphviz errors in unit tests
    test_ignore_graphviz_errors = True
    
    # Ignore the known failures
    test_include_primitivedps_knownfailures = False
    
    # only draw 1/20th of pictures
    test_fraction_of_allreports = 0.025
     
    test_insist_correct_html_from_ast_to_html = False
    #
    # UI
    #
    
    # Affects things like Nat
    use_unicode_symbols = True
#     if not use_unicode_symbols:
#         msg =( 'Note that use_unicode_symbols is false, which is not suitable for printing')
#         warnings.warn(msg)

    # Any time we need to solve a relation like (r1*r2==f),
    # we will bound r1 and r2 in the interval [eps, 1/eps].
    inv_relations_eps = np.finfo(float).eps # ~1e-16
    # TODO: think whether this makes us optimistic or pessimistic, and where
    
    # threshold above which we output a warning
    parsing_too_slow_threshold = 0.5

    log_cache_writes = False
    
    InvPlus2Nat_max_antichain_size=  100000
    InvMult2Nat_memory_limit   = 10000
    
    # Actually write to disk the reports
    test_allformats_report_write = False
    
    # this can be changed by customer. The other configuration switches
    # are all relative.
    diagrams_fontsize = 14

    diagrams_smallimagesize_rel = 0.4
    diagrams_leqimagesize_rel = 0.3
    diagrams_bigimagesize_rel = 60  
    
    # how much to scale the produced svg from dots
    # if diagrams_fontsize = 14 and you want the font to be 10,
    # use 10.0
    svg_apparent_fontsize = 10.0 
    scale_svg = svg_apparent_fontsize / float(diagrams_fontsize)
    
    # useful for debugging css
    # for (1) manual and (2) mcdp-render
    manual_link_css_instead_of_including = True
    
    
#     pdf_to_png_dpi = 300 # dots per inch
    pdf_to_png_dpi = 100 # dots per inch
    
    docs_xml_allow_empty_attributes = ['np', 'noprettify', 'nonumber', 'notoc',
                                        'mcdp-value', 'mcdp-poset']

    # directories ignored by locate_files
    locate_files_ignore_patterns = ['node_modules', '.git', 'commons', '_cached', 
                                    '_mcdpweb_cache', 'resized', 
                                    '1301-jbds-figures', 'out', 'out-html', 'reprep-static',
                                    '*.html_resources', 'out-*', 'compmake', '*.key']

    # images used to look for icons for DPs 
    exts_for_icons = ('png', 'jpg', 'PNG', 'JPG', 'jpeg', 'JPEG') # XXX
    # all images 
    exts_images = exts_for_icons + ('svg', 'SVG', 'pdf', 'PDF')
    
    ENV_TEST_LIBRARIES = 'MCDP_TEST_LIBRARIES'
    ENV_TEST_LIBRARIES_EXCLUDE = 'MCDP_TEST_LIBRARIES_EXCLUDE'
    ENV_TEST_SKIP_MCDPOPT = 'MCDP_TEST_SKIP_MCDPOPT'
    
    
    
    # deprecated, used as attr for implementation spaces
    ATTRIBUTE_NDP_RECURSIVE_NAME = 'ndp_recursive_name'
    
    # added to NamedDPs
    ATTRIBUTE_NDP_MAKE_FUNCTION = 'make'
    
    # added 
    ATTR_LOAD_NAME = '__mcdplibrary_load_name'
    ATTR_LOAD_LIBNAME = '__mcdplibrary_load_libname'
    ATTR_LOAD_REALPATH = '__mcdplibrary_load_realpath'
    
    log_duplicates = False

        
    
    shelf_extension = 'mcdpshelf'
    shelf_desc_file = 'mcdpshelf.yaml'
    library_extension = 'mcdplib'
    