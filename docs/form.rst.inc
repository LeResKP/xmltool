Form
====


Generating a HTML form
-----------------------

.. testsetup:: *

    from lxml import etree
    import xmltool


We will make this example with the same XML file:


.. include:: examples/movie.xml
    :code: xml

Now we will genererate the HTML form:
    >>> xml_filename = 'examples/movie.xml'
    >>> html = xmltool.generate_form(xml_filename)
    >>> # Use etree to have a nicer HTML. In other case we don't need to use it directly.
    >>> xml = etree.fromstring(html)
    >>> html = etree.tostring(xml.getroottree(), pretty_print=True, encoding='UTF-8', method="html")
    >>> open('examples/movie.html', 'w').write(html)

See the generated HTML:

.. include:: examples/movie.html
    :code: html

.. note:: `Click here <examples/movie-full.html>`_ to see the rendering with the javascript included.


Submitting a HTML form
----------------------

XML tool support you submit WebOb request or dict. We will use a dict for this example.

    >>> xml_filename = 'examples/my-movie.xml'
    >>> dic = {'_xml_dtd_url': 'http://xmltool.lereskp.fr/examples/movie.dtd',
    ...        '_xml_encoding': 'UTF-8',
    ...        'movie:title:_value': 'My movie title',
    ...        'movie:realisator:_value': 'My movie realisator',
    ...        'movie:characters:character__list:1:character:_value': 'My first character',
    ...        'movie:characters:character__list:2:character:_value': 'My second character',
    ...       }
    >>> obj = xmltool.update(xml_filename, dic)
    >>> print obj.title._value
    My movie title
    >>> print obj.characters.character[0]._value
    My first character

The generated XML looks like:

.. include:: examples/my-movie.xml
    :code: xml

.. note:: Before writing the XML file, it is validated according to the DTD file
