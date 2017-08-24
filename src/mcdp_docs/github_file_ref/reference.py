from collections import namedtuple
from contracts import contract
from contracts.utils import raise_wrapped
from comptests.registrar import run_module_tests, comptest
import urllib2


# Consider an URL of the type
# github:org=duckietown,repo=Software,path=![path],branch=branch,frag=frag
# 
# The keys:
# 
#     org
#     repo
#     path
#     branch
#     frag
#     line
# contents
# url

GithubFileRef = namedtuple('GithubFileRef', 
                           ['org', 'repo', 'path', 'branch', 
                            'from_line', 'to_line',
                            'from_text', 'to_text',
                            'contents', 'url'])

class InvalidGithubRef(ValueError):
    pass

@contract(s=str)
def parse_github_file_ref(s):
    """ 
        Parses a line of the type
    
        github:k=v,k=v
        
    """
    prefix = 'github:'
    try:
        if not s.startswith(prefix):
            msg = 'URL does not start with prefix %r.' % prefix
            raise InvalidGithubRef(msg)
        
        values = {}
        then = s[len(prefix):]
        pairs = then.split(',')
        #print 'pairs', pairs
        if not pairs:
            msg = 'Empty url'
            raise InvalidGithubRef(msg)
        for p in pairs:
            if not '=' in p:
                msg = 'Invalid pair %r'% p
                raise InvalidGithubRef(msg)
            i = p.index('=')
            k = p[:i]
            v = p[i+1:]
            if not v or not k:
                msg = 'Invalid pair %r.' % p
                raise InvalidGithubRef(msg)
            values[k] = v
        
        org = values.pop('org', None)
        repo = values.pop('repo', None)
        branch = values.pop('branch', None)
        from_text = values.pop('from_text', None)
        if from_text is not None:
            from_text = urllib2.unquote(from_text)
        to_text = values.pop('to_text', None)
        if to_text is not None:
            to_text = urllib2.unquote(to_text)
        from_line = values.pop('from_line', None)
        if from_line is not None:
            from_line = int(from_line)
        to_line = values.pop('to_line', None)
        if to_line is not None:
            to_line = int(to_line)
        path = values.pop('path', None)
        
        if from_line is not None and from_text is not None:
            msg = 'You cannot give both a line number and a fragment.'
            raise InvalidGithubRef(msg)
        
        if to_line is not None and to_text is not None:
            msg = 'You cannot give both a line number and a fragment.'
            raise InvalidGithubRef(msg)
    
        to_given = (to_line is not None) or (to_text is not None) 
        from_given = (from_line is not None) or (from_text is not None)
        
        if to_given and not from_given:
            msg = 'Cannot specify the end of a fragment but not the start.'
            raise InvalidGithubRef(msg)
        if values:
            msg = 'Additional keys %s' % sorted(values)
            raise InvalidGithubRef(msg)
        
        return GithubFileRef(org=org, repo=repo, branch=branch,
                             from_text=from_text, to_text=to_text, 
                             from_line=from_line, to_line=to_line, 
                             
                             path=path, contents=None,
                             url=None)
    except InvalidGithubRef as e:
        msg = 'Cannot parse "%s":' % s
        raise_wrapped(InvalidGithubRef, e, msg, compact=True)
    

def expect_failure(s):
    try:
        parse_github_file_ref(s)
    except InvalidGithubRef:
        pass
    else:
        raise Exception('expected failure for %r' % s)
    
@comptest
def parse1():
    expect_failure('github')
    expect_failure('github:')
    expect_failure('github:path=')
    expect_failure('github:path=,')
    expect_failure('github:,')
    expect_failure('github:notexist=one')
    expect_failure('github:from_line=1,from_text=ciao')
    expect_failure('github:to_line=1') # to without from
        
@comptest
def parse2():
    s = 'github:path=name'
    r = parse_github_file_ref(s)
    assert r.path == 'name'
    s = 'github:org=name'
    r = parse_github_file_ref(s)
    assert r.org == 'name'        
    s = 'github:branch=name'
    r = parse_github_file_ref(s)
    assert r.branch == 'name'        
    s = 'github:from_line=3'
    r = parse_github_file_ref(s)
    assert r.from_line == 3        
    s = 'github:from_text=3'
    r = parse_github_file_ref(s)
    assert r.from_text == '3'        
    s = 'github:from_line=0,to_line=3'
    r = parse_github_file_ref(s)
    assert r.to_line == 3        
    s = 'github:from_text=1,to_text=3'
    r = parse_github_file_ref(s)
    assert r.to_text == '3'        
    
    s = 'github:from_text=ciao%20come'
    r = parse_github_file_ref(s)
    assert r.from_text == "ciao come"        
    
    s = 'github:from_text=3,to_line=1'
    r = parse_github_file_ref(s)
    s = 'github:from_line=3,to_text=1'
    r = parse_github_file_ref(s)
    s = 'github:from_text=3,to_text=1'
    r = parse_github_file_ref(s)
    s = 'github:from_line=3,to_line=1'
    r = parse_github_file_ref(s)
    

if __name__ == '__main__':
    run_module_tests()
    
    