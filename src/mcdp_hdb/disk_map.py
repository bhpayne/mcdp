from collections import defaultdict
import copy
import datetime
import os
import sys

from contracts import contract
from contracts.interface import describe_value
from contracts.utils import raise_desc, raise_wrapped, indent, check_isinstance

from mcdp.logs import logger_tmp, logger
from mcdp_hdb.disk_struct import ProxyDirectory, ProxyFile
from mcdp_hdb.schema import SchemaHash, SchemaString, SchemaContext,\
    SchemaList, SchemaBytes, NOT_PASSED, SchemaDate, SchemaBase
# from mcdp_library_tests.create_mockups import mockup_flatten
from mcdp_utils_misc import format_list
from mcdp_utils_misc.my_yaml import yaml_dump, yaml_load


class IncorrectFormat(Exception):
    pass


def raise_incorrect_format(msg, schema, data):
    msg2 = 'Incorrect format:\n'
    msg2 += indent(msg, '  ') 
    if isinstance(data, str):
        datas = data
    else:
        datas = yaml_dump(data).encode('utf8')
    MAX = 512
    if len(datas) > MAX:
        datas = datas[:MAX] + ' [truncated]'
    if False:
        msg2 += '\nData:\n'
        msg2 += indent(datas, '  ')
    #     msg2 += 'repr: '+ datas.__repr__()
    raise_desc(IncorrectFormat, msg2, schema=schema)
 
class HintExtensions():
    def __init__(self, extensions):
        self.extensions = extensions

    def __repr__(self):
        return 'HintExtensions(%r)' % self.extensions
    
class HintFile():
    def __init__(self, pattern='%'):
        self.pattern = pattern

    def __repr__(self):
        return 'HintFile(%r)' % self.pattern

class HintStruct():
    def __init__(self):
        pass
    def __repr__(self):
        return 'HintStruct()'
            
class HintDir():
    def __init__(self, pattern='%'):
        self.pattern = pattern
 
    def __repr__(self):
        return 'HintDir(%r)' % self.pattern

class HintFileYAML():
    def __init__(self, pattern='%'):
        self.pattern = pattern
    def __repr__(self):
        return 'HintFileYAML(%r)' % self.pattern
        
class DiskMap():

    def __init__(self):
        self.hints = {}

        self.inside_yaml = False
        self.hint_translation = defaultdict(lambda: dict())

    def get_hint(self, s):
        check_isinstance(s, SchemaBase)
        if self.inside_yaml:
            return HintStruct()
        if s in self.hints:
            return self.hints[s]
        if isinstance(s, SchemaString):
            return HintFile()
        if isinstance(s, SchemaBytes):
            return HintFile()
        if isinstance(s, SchemaHash):
            return HintDir()
        if isinstance(s, SchemaContext):
            return HintDir()
        if isinstance(s, SchemaList):
            return HintDir()
        if isinstance(s, SchemaDate):
            return HintFile()
        msg = 'Cannot find hint for %s' % describe_value(s)
        raise ValueError(msg)

    def translate_children(self, s, dic):
        self.hint_translation[s].update(**dic)

    def hint_directory(self, s, pattern='%'):
        self.hints[s] = HintDir(pattern)

    def hint_extensions(self, s, extensions):
        self.hints[s] = HintExtensions(extensions)

    def hint_file(self, s, pattern='%'):
        if isinstance(s, SchemaHash):
            if not '%' in pattern:
                raise ValueError(s)
        self.hints[s] = HintFile(pattern)

    def hint_file_yaml(self, s, pattern='%'):
        self.hints[s] = HintFileYAML(pattern)

    @contract(fh=ProxyDirectory)
    def interpret_hierarchy(self, schema, fh):
        '''
            fh = Files in recursive dictionary format:
            {'dir': {'file': 'filecontents'}} 
        '''
        try:
            return self.interpret_hierarchy_(schema, fh=fh)
        except IncorrectFormat as e:
            msg = 'While parsing: \n'
            msg += indent(str(schema), ' ')
            msg += '\n\nfiles:\n\n'
            msg += indent(fh.tree(), '  ')
            raise_wrapped(IncorrectFormat, e, msg)

    @contract(fh='isinstance(ProxyDirectory)|isinstance(ProxyFile)')
    def interpret_hierarchy_(self, schema, fh):
        try:
            hint = self.get_hint(schema)

            if isinstance(schema, SchemaHash):
                if isinstance(hint, HintDir):
                    return read_SchemaHash_SER_DIR(self, schema, fh)
                if isinstance(hint, HintExtensions):
                    return read_SchemaHash_Extensions(self, schema, fh)

            if isinstance(schema, SchemaContext):
                if isinstance(hint, HintDir):
                    return read_SchemaContext_SER_DIR(self, schema, fh)
                elif isinstance(hint, HintStruct):
                    return read_SchemaContext_SER_STRUCT(self, schema, fh)
                if isinstance(hint, HintFileYAML):
                    return read_SchemaContext_SER_FILE_YAML(self, schema, fh)

            if isinstance(schema, SchemaString):
                return fh.contents

            if isinstance(schema, SchemaList):
                if isinstance(hint, HintDir):
                    return interpret_SchemaList_SER_DIR(self, schema, fh)
                elif isinstance(hint, HintStruct):
                    return interpret_SchemaList_SER_STRUCT(self, schema, fh)
                return fh.contents

            if isinstance(schema, SchemaBytes):
                return fh.contents

            if isinstance(schema, SchemaDate):
                if isinstance(fh, datetime.datetime):
                    return fh.contents
                else:
                    logger_tmp.debug('looking at %r' % fh)
                    return yaml_load(fh)

            msg = 'NotImplemented'
            raise_desc(NotImplementedError, msg, schema=type(schema), hint=hint)
        except IncorrectFormat as e:
            msg = 'While interpreting schema %s' % type(schema)
            msg += ', hint: %s' % str(self.get_hint(schema))
            raise_wrapped(IncorrectFormat, e, msg, compact=True, 
                          exc = sys.exc_info())

    @contract(returns=ProxyDirectory)
    def create_hierarchy(self, schema, data):
        return self.create_hierarchy_(schema=schema, data=data)

    def create_hierarchy_(self,  schema, data):
        hint = self.get_hint(schema)
        
        if isinstance(hint, HintFileYAML):
            return ProxyFile(yaml_dump(data))

        if isinstance(schema, SchemaHash):
            if isinstance(hint, HintDir):
                return write_SchemaHash_SER_DIR(self, schema, data)
            if isinstance(hint, HintExtensions):
                return write_SchemaHash_Extensions(self, schema, data)
            
        if isinstance(schema, SchemaList):
            if isinstance(hint, HintDir):
                return write_SchemaList_SER_DIR(self, schema, data)
            
        if isinstance(schema, SchemaContext):
            if isinstance(hint, HintDir):
                return write_SchemaContext_SER_DIR(self, schema, data)
    
        # inside yaml
        if isinstance(schema, SchemaString):
            return ProxyFile(data)

        if isinstance(schema, SchemaList):
            return data # XXXX

        if isinstance(schema, SchemaBytes):
            return ProxyFile(data)
        
        if isinstance(schema, SchemaDate):
            return ProxyFile(yaml_dump(data))
        
        msg = 'Not implemented for %s, hint %s' % (schema, hint)
        raise ValueError(msg)

class NotKey(Exception):
    pass

def key_from_filename(pattern, filename):
    if not '%' in pattern:
        msg = 'Cannot get key from filename.'
        raise_desc(IncorrectFormat, msg, pattern=pattern, filename=filename)
        
    if pattern.startswith('%'):
        key = filename.replace(pattern.replace('%', ''), '')
        
        filename2 = pattern.replace('%', key)
        if filename2 != filename:
            msg = 'Filename "%s" does not follow pattern "%s".' % (filename, pattern)
            raise NotKey(msg)
        return key
    else:
        raise NotImplementedError(pattern)


def write_SchemaList_SER_DIR(self, schema, data):
    check_isinstance(schema, SchemaList)
    hint = self.get_hint(schema)
    res = ProxyDirectory()
    for i, d in enumerate(data):
        filename = hint.pattern.replace('%', str(i))
        res[filename] = self.create_hierarchy_(schema.prototype, d)
    return res


def interpret_SchemaList_SER_STRUCT(self, schema, data):
    check_isinstance(schema, SchemaList)
    check_isinstance(data, list)
    n = len(data)
    res = [None] * n
    for i, x in enumerate(data):
        res[i] = self.interpret_hierarchy_(schema.prototype, x)
    return res


def interpret_SchemaList_SER_DIR(self, schema, fh):
    check_isinstance(schema, SchemaList)
    n = len(fh)
    res = [None] * n
    for filename in fh:
        try:
            i = int(filename)
        except ValueError:
            msg = 'Filename "%s" does not represent a number.' % filename
            raise_incorrect_format(msg, schema, fh)
        if not (0 <= i < n):
            msg = 'Integer %d is not in the bounds (n = %d).' % (i, n)
            raise_incorrect_format(msg, schema, fh)

        res[i] = self.interpret_hierarchy_(schema.prototype, fh[filename])
    return res

@contract(fh=ProxyDirectory)
def read_SchemaHash_Extensions(self, schema, fh):
    check_isinstance(schema, SchemaHash)
    res = {}
    extensions = self.get_hint(schema).extensions 
            
    found = [] 
    for filename, data in fh.recursive_list_files():
        found.append(filename)

        name, ext = os.path.splitext(filename)
        if not ext:
            continue
        ext = ext[1:]
        
        if ext in extensions: 
            if not name in res:
                res[name] = {}
            res[name][ext] = self.interpret_hierarchy_(schema.prototype[ext], data)
            # fill nulls for other extensions
            for ext2 in extensions:
                if not ext2 in res[name]: # do not overwrite
                    res[name][ext2] = None 
    return res

def read_SchemaHash_SER_DIR(self, schema, fh):
    check_isinstance(schema, SchemaHash)
    res = {}
    hint = self.get_hint(schema)
    if hint.pattern == '%':
        seq = fh.items()
    else:
        seq = recursive_list(fh, hint.pattern)
 
    seq = list(seq)
    msg = 'read_SchemaHash_SER_DIR\n'
    msg += indent(fh.tree(0), 'files  ') + '\n'
    msg += 'pattern is %r\n' % hint.pattern
    msg += 'list is %s\n' % seq
    #logger.info(msg)
    
    for filename, data in seq:
        try:
            k = key_from_filename(pattern=hint.pattern, filename=filename)
        except NotKey:
            logger.warning('Ignoring file "%s": not a key' % filename)
            continue
        assert not k in res, (k, hint.pattern, filename)
        
        try:
            res[k] = self.interpret_hierarchy_(schema.prototype, data)
        except IncorrectFormat as e:
            msg = 'While interpreting filename "%s":' % filename
            raise_wrapped(IncorrectFormat, e, msg, compact=True, exc=sys.exc_info())
             
    return res

def recursive_list(fh, pattern):
    for filename, data in fh.items():
        if isinstance(data, dict):
            for x in recursive_list(data, pattern):
                yield x
        try: 
            key_from_filename(pattern=pattern, filename=filename)
            yield filename, data
        except NotKey:
            pass
        
@contract(returns=ProxyDirectory)
def write_SchemaHash_SER_DIR(self, schema, data):
    check_isinstance(schema, SchemaHash)
    check_isinstance(data, dict)
    res = ProxyDirectory()
    hint = self.get_hint(schema)
    for k in data:
        filename = hint.pattern.replace('%', k)
        assert not filename in res, (k, hint.pattern, filename)
        res[filename] = self.create_hierarchy_(schema.prototype, data[k])
    return res

@contract(returns=ProxyDirectory)
def write_SchemaHash_Extensions(self, schema, data):
    check_isinstance(schema, SchemaHash)
    check_isinstance(data, dict)
    res = ProxyDirectory()
    hint = self.get_hint(schema) 
    for k in data:
        for ext in hint.extensions:
            filedata = data[k][ext]
            if filedata is not None:
                filename = '%s.%s' % (k, ext)
                res[filename] = self.create_hierarchy_(schema.prototype[ext], filedata)
    return res

def filename_for_k_SchemaContext_SER_DIR(self, schema, k):
    dic = self.hint_translation[schema]
    filename = dic.get(k, k)
    return filename

@contract(f=ProxyFile)
def read_SchemaContext_SER_FILE_YAML(self, schema, f):
    data = yaml_load(f.contents)
    res = {}
    present = set(data)
    used = set()
    for k, schema_child in schema.children.items():
        if k in data:
            # have it
            pass
        else:
            # dont' have it
            default = schema_child.get_default()
            if default != NOT_PASSED:
                # use default
                res[k] = copy.copy(schema_child.default)
                logger.warning('Using default for key %s' % k)
                continue
            else:
                # no default
                msg = 'Expected key "%s".' % k
                raise_incorrect_format(msg, schema, data)
        used.add(k)
        res[k] = data[k]
#         self.inside_yaml = True
#         try:
#             res[k] = self.interpret_hierarchy_(schema_child, data[k])
#         finally:
#             self.inside_yaml = False
    extra = set(present) - set(used)

    if extra:
        msg = 'Extra fields: %s.' % format_list(sorted(extra))
        msg += '\nPresent: %s' % format_list(present)
        msg += '\nUsed: %s' % format_list(used)
        raise_incorrect_format(msg, schema, data)
    schema.validate(res)
    return res


def read_SchemaContext_SER_STRUCT(self, schema, fh):
    res = {}
    remaining = set(fh)
    for k, schema_child in schema.children.items():
        if not k in fh:
            default = schema_child.get_default()
            if default != NOT_PASSED:
                res[k] = copy.copy(default)
                logger.debug('Using default for key %s' % k)
            else:
                msg = 'Expected element "%s".' % k
                raise_incorrect_format(msg, schema, fh)
        else:
            res[k] = self.interpret_hierarchy_(schema_child, fh[k])
            remaining.remove(k)
    if remaining:
        msg = 'Extra keys: %s' % format_list(remaining)
        raise_incorrect_format(msg, schema, fh)
    schema.validate(res)
    return res


def read_SchemaContext_SER_DIR(self, schema, fh):
    if not isinstance(fh, ProxyDirectory):
        msg = 'I expected a ProxyDirectory representing dir entries.'
        msg += indent(str(schema), 'schema ')
        raise_desc(IncorrectFormat, msg, fh=fh)
    res = {}
    for k, schema_child in schema.children.items():
        filename = filename_for_k_SchemaContext_SER_DIR(self, schema, k)
        if filename is None:
            # skip directory
            res[k] = self.interpret_hierarchy_(schema_child, fh)
        else:
            if not filename in fh:
                default = schema_child.get_default()
                if default != NOT_PASSED:
                    res[k] =copy.copy( default)
                    logger.debug('Using default for key %s' % k)
                else:
                    msg = 'Expected filename "%s".' % filename
                    msg += '\n available: %s' % format_list(fh)
                    raise_incorrect_format(msg, schema, fh)
            else:
                try:
                    res[k] = self.interpret_hierarchy_(schema_child, fh[filename])
                except IncorrectFormat as e:
                    msg = 'While interpreting child "%s", filename "%s":' % (k, filename)
                    raise_wrapped(IncorrectFormat, e, msg, compact=True, exc=sys.exc_info())
    schema.validate(res)
    return res
 
@contract(returns=ProxyDirectory)
def write_SchemaContext_SER_DIR(self, schema, data):
    res = ProxyDirectory()
    for k, schema_child in schema.children.items():
        rec = self.create_hierarchy_(schema_child, data[k])
        filename = filename_for_k_SchemaContext_SER_DIR(self, schema, k)
        if filename is None:
            for kk, vv in rec.items():
                if kk in res:
                    msg = 'Already set file %r' % kk
                    raise Exception(msg)
                res[kk] = vv 
        else:
            if filename in res:
                msg = 'I already saw filename "%s".' % filename
                raise_incorrect_format(msg, schema, data)
            res[filename] = rec
    return res
