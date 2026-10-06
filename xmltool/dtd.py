from io import StringIO, open
from dogpile.cache.api import NO_VALUE
from lxml import etree
import os
import requests
import tempfile
import threading


from . import dtd_parser
from . import cache


class ValidationError(Exception):
    pass


# Compiled etree.DTD objects, keyed by the dtd content. It's per thread since
# etree.DTD stores the error_log of the last validation on the object.
_compiled_dtds = threading.local()


class DTD(object):
    def __init__(self, url, path=None):
        """
        url: the url to get the dtd, it can be http or filesystem resources
        path is used in case the dtd use relative filesystem path
        """
        self._parsed_dict = None
        if isinstance(url, StringIO):
            self.url = None
            # set _content and validation
            # self_content should be str
            self._content = url.getvalue()
            self.validate()
        else:
            self.url = url
            self.path = path
            self._content = None

    def _get_dtd_url(self):
        if self.url.startswith("http://") or self.url.startswith("https://"):
            return self.url

        url = self.url
        if (
            self.path
            and not self.url.startswith("/")
            and not self.url.startswith(self.path)
        ):
            url = os.path.join(self.path, self.url)
        return url

    def _fetch(self):
        """Fetch the dtd content"""
        url = self._get_dtd_url()
        if url.startswith("http://") or url.startswith("https://"):
            res = requests.get(url, timeout=5)
            # Use res.text to have str
            self._content = res.text
        else:
            # TODO: Get encoding from the dtd file (xml tag).
            self._content = open(url, "r").read()
        return self._content

    @property
    def content(self):
        """The dtd content"""
        if self._content:
            return self._content
        if cache.CACHE_TIMEOUT is None:
            return self._fetch()

        assert self.url
        cache_key = "xmltool.get_dtd_content.%s" % (self._get_dtd_url())
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
        f, filename = tempfile.mkstemp()
        # Don't know why but the validation doesn't work using a StringIO so we
        # write a temporary file
        try:
            try:
                # TODO: Get encoding from the dtd file (xml tag).
                os.write(f, content.encode("utf-8"))
            finally:
                os.close(f)
            dtd_obj = etree.DTD(filename)
        finally:
            os.remove(filename)

        if dtd_obj.error_log:
            raise ValidationError(dtd_obj.error_log)
        # It can raise an exception if something is wrong in the dtd
        # For example, etree.DTD doesn't raise exception if a sub element is
        # not defined, self.parse does.
        self.parse()

    def _parse(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.content)
        self._parsed_dict = dtd_parser._create_classes(dtd_dict)
        return self._parsed_dict

    def parse(self):
        if self._parsed_dict:
            return self._parsed_dict

        if cache.CACHE_TIMEOUT is None:
            return self._parse()

        cache_key = "xmltool.parse.%s" % self.url if self.url else None

        if not cache_key:
            return self._parse()

        value = cache.region.get(cache_key, cache.CACHE_TIMEOUT)
        if value is not NO_VALUE:
            return value
        value = self._parse()
        cache.region.set(cache_key, value)
        return value

    def validate_xml(self, xml_obj):
        """Validate an XML object

        :param xml_obj: The XML object to validate
        :type xml_obj: etree.Element
        :param dtd_str: The dtd to use for the validation
        :type dtd_str: str
        :return: True. Raise an exception if the XML is not valid
        :rtype: bool
        """
        self._get_compiled_dtd().assertValid(xml_obj)
        return True

    def _get_compiled_dtd(self):
        """Get the compiled etree.DTD, the dtd is validated and compiled only
        once per content"""
        content = self.content
        cache_dict = getattr(_compiled_dtds, "value", None)
        if cache_dict is None:
            cache_dict = _compiled_dtds.value = {}
        dtd_obj = cache_dict.get(content)
        if dtd_obj is None:
            # Make sure the dtd is valid
            self.validate()
            dtd_obj = etree.DTD(StringIO(content))
            cache_dict[content] = dtd_obj
        return dtd_obj
