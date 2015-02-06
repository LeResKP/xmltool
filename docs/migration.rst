#########
Migration
#########


When the dtd has been updated, if there are some new required elements, we have to update the XML files as well.  Since we can load an existing XML file without validating it, it's very easy to update it.


Updating a XML file after a dtd change
---------------------------------------

We use the same dtd as before:

.. include:: examples/movies.dtd
    :code: dtd


We just put the date element as required

.. include:: examples/movies-new.dtd
    :code: dtd

.. testsetup::

    filename = 'examples/tutorial1.xml'
    xml = open(filename, 'r').read()
    xml = xml.replace('movies.dtd', 'movies-new.dtd')
    open('examples/migration.xml', 'w').write(xml)


The XML doesn't have the date defined:

.. include:: examples/migration.xml
    :code: xml


.. doctest::

    >>> import xmltool
    >>> filename = 'examples/migration.xml'
    >>> # It fails since by default we validate the XML follows the DTD
    >>> obj = xmltool.load(filename)
    Traceback (most recent call last):
    ...
    DocumentInvalid:
    >>> obj = xmltool.load(filename, validate=False)
    >>> # The date tag is automatically added when generating the XML
    >>> print obj
    <movies>
      <movie>
        <title>Titanic</title>
        <date></date>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
        <good-comment>My comment 1</good-comment>
        <bad-comment>My comment 2</bad-comment>
      </movie>
    </movies>
    <BLANKLINE>
