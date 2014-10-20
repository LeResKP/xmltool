import os
from dogpile.cache import make_region


CACHE_TIMEOUT = None
if os.environ.get('XMLTOOL_CACHE_TIMEOUT'):
    try:
        CACHE_TIMEOUT = int(os.environ.get('XMLTOOL_CACHE_TIMEOUT'))
    except ValueError:
        # TODO: add logging
        pass

# Use to put some cache
region = make_region().configure("dogpile.cache.memory")
