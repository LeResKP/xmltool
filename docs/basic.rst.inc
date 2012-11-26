Basic
=====


Loading a XML file
-------------------

For this example we will load the following XML file:

.. include:: examples/movie.xml
    :code: xml

.. testsetup:: *

    from xmltools import dtd_parser

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = dtd_parser.get_obj(xml_filename)
    >>> print obj.attrs
    {'idmovie': 'M1'}
    >>> print obj #doctest: +ELLIPSIS
    <xmltools.dtd_parser.movie object at 0x...>
    >>> print obj.title.value
    Full Metal Jacket
    >>> print obj.characters.character[0].value
    Matthew Modine
    >>> print obj.characters.character[0].attrs
    {'idcharacter': 'C1'}

.. warning:: For now if you want to access to the property containing a dash '**-**' you should use the **getattr** builtin.


Writing a XML file
-------------------

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = dtd_parser.get_obj(xml_filename)
    >>> obj.title.value += ' updated'
    >>> obj.write('examples/movie-updated.xml')

See the content of the new XML file:

.. include:: examples/movie-updated.xml
    :code: xml


Updating a XML file after a dtd change
---------------------------------------

Our dtd file:

.. include:: examples/movie.dtd
    :code: dtd

Now we add a comment field required. In XML the tag is required, not the content!

.. include:: examples/movie-1.dtd
    :code: dtd

Use the new DTD file in our XML file. You don't need to create a new DTD file when you want to update it, it's just needed to write this example easily.

.. include:: examples/movie-1.xml
    :code: xml


To update the file according to the DTD change, we just need to load it without validating the XML and write it.  Xmltools detects the missing tags and add it!

    >>> xml_filename = 'examples/movie-1.xml'
    >>> obj = dtd_parser.get_obj(xml_filename, validate_xml=False)
    >>> obj.write('examples/movie-1-updated.xml')

You can see that the comment tag is added automatically:

.. include:: examples/movie-1-updated.xml
    :code: xml
