Form
====


Generating a HTML form
-----------------------

.. testsetup:: *

    from lxml import etree


We will make this example with the same XML file:


.. include:: examples/movie.xml
    :code: xml

Now we will genererate the HTML form:
    >>> xml_filename = 'examples/movie.xml'
    >>> html = dtd_parser.generate_form(xml_filename)
    >>> # Use etree to have a nicer HTML. In other case we don't need to use it directly.
    >>> xml = etree.fromstring(html)
    >>> html = etree.tostring(xml.getroottree(), pretty_print=True, encoding='UTF-8', method="html")
    >>> open('examples/movie.html', 'w').write(html)

See the generated HTML:

.. include:: examples/movie.html
    :code: html

.. note:: `Click here <examples/movie.html>`_ to see the rendering.
