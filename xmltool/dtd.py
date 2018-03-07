from dogpile.cache.api import NO_VALUE
from lxml import etree
import os
import requests
import tempfile


from . import cache


class ValidationError(Exception):
    pass


class DTD(object):

    def __init__(self, url, path=None):
        """
        url: the url to get the dtd, it can be http or filesystem resources
        path is used in case the dtd use relative filesystem path
        """
        self.url = url
        self.path = path
        self._content = None

    def _fetch(self):
        """Fetch the dtd content
        """
        if self.url.startswith('http://') or self.url.startswith('https://'):
            res = requests.get(self.url, timeout=5)
            # Use res.content instead of res.text because we want string. If we
            # get unicode, it fails when creating classes with type().
            self._content = res.content
        else:
            url = self.url
            if (self.path and
                    not self.url.startswith('/') and
                    not self.url.startswith(self.path)):
                url = os.path.join(self.path, self.url)
            self._content = open(url, 'r').read()
        return self._content

    @property
    def content(self):
        """The dtd content
        """
        if self._content:
            return self._content
        if cache.CACHE_TIMEOUT is None:
            return self._fetch()

        cache_key = 'xmltool.get_dtd_content.%s.%s' % (self.url, self.path)
        value = cache.region.get(cache_key, cache.CACHE_TIMEOUT)
        if value is not NO_VALUE:
            return value
        content = self._fetch()
        self.validate()
        cache.region.set(cache_key, content)
        return content

    def validate(self):
        """Validate the dtd is valid

        It raises a ValidationError exception when not valid
        It also can raise etree.ParseError if the dtd is unparsable
        """
        # Be careful when getting the content we can have a recursive loop
        # since we validate the dtd when getting it. But we also want to be
        # able to validate a dtd before we fetch the content.
        content = self._content if self._content else self.content
        __, filename = tempfile.mkstemp()
        # Don't know why but the validation doesn't work using a StringIO so we
        # write a temporary file
        with open(filename, 'w') as f:
            f.write(content)
        dtd_obj = etree.DTD(filename)
        if dtd_obj.error_log:
            raise ValidationError(dtd_obj.error_log)
