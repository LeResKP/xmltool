#!/usr/bin/env python

import re
import six
import webob


# This hack helps work with different versions of WebOb
if not hasattr(webob, 'MultiDict'):
    webob.MultiDict = webob.multidict.MultiDict


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def truncate(s, limit=30):
    limit += 1
    if len(s) > limit:
        s = s[:limit]
        for i in range(len(s), 0, -1):
            if s[i-1] == ' ':
                return s.rstrip() + '...'
            s = s[:-1]
    return s


def prefixes_to_str(lis):
    return ':'.join(lis)


# Basically the same function as in tw2.core.validation.
# We don't want to have a lot of dependancies just for this function.
def unflatten_params(params):
    """This performs the first stage of validation. It takes a dictionary where
    some keys will be compound names, such as "form:subform:field" and converts
    this into a nested dict/list structure. It also performs unicode decoding.
    """
    if isinstance(params, webob.MultiDict):
        params = params.mixed()
    # TODO: the encoding can be in the given params, use it!
    enc = 'utf-8'
    for p in params:
        if isinstance(params[p], str) and six.PY2:
            # Can raise an exception!
            params[p] = params[p].decode(enc)

    out = {}
    for pname in params:
        dct = out
        elements = pname.split(':')
        for e in elements[:-1]:
            dct = dct.setdefault(e, {})
        dct[elements[-1]] = params[pname]

    numdict_to_list(out)
    return out


number_re = re.compile('^\d+$')


def numdict_to_list(dct):
    for k, v in dct.items():
        if isinstance(v, dict):
            numdict_to_list(v)

            if all(number_re.match(k) for k in v):
                lis = []
                if v:
                    for index in range(int(max(map(int, v.keys()))) + 1):
                        value = None
                        if str(index) in v:
                            value = v[str(index)]
                        lis += [value]
                dct[k] = lis
