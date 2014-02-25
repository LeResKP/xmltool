Basic
=====

Creating a XML
-------------------

General case
^^^^^^^^^^^^

You will see in this example how it's easy to create an XML file according to the following DTD file:

.. include:: examples/movie.dtd
    :code: dtd


.. doctest::

    >>> from lxml import etree
    >>> import xmltool
    >>> from xmltool import dtd_parser
    >>> dtd_url = 'http://xmltool.lereskp.fr/examples/movie.dtd'
    >>> dic = dtd_parser.parse(dtd_url=dtd_url)
    >>> movie = dic['movie']()
    >>> title = movie.add('title', 'Movie title')
    >>> print title.text
    Movie title
    >>> realisator = movie.add('realisator', 'realisator name')
    >>> characters = movie.add('characters')
    >>> c1 = characters.add('character', 'character 1')
    >>> c2 = characters.add('character', 'character 2')
    >>> print etree.tostring(movie.to_xml(), pretty_print=True)
    <movie>
      <title>Movie title</title>
      <realisator>realisator name</realisator>
      <characters>
        <character>character 1</character>
        <character>character 2</character>
      </characters>
    </movie>
    <BLANKLINE>


Case with conditional elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we will see how to handle case with some conditional elements. It's '(qcm|mqm)*' in the following DTD files:

.. include:: examples/exercise.dtd
    :code: dtd


.. doctest::

    >>> import xmltool
    >>> from xmltool import dtd_parser
    >>> dtd_url = 'http://xmltool.lereskp.fr/examples/exercise.dtd'
    >>> dic = dtd_parser.parse(dtd_url=dtd_url)
    >>> exercise = dic['Exercise']()
    >>> question = exercise.add('question', 'the question')
    >>> qcm = exercise.add('qcm')
    >>> # Now we can't add a mqm since a qcm exists
    >>> exercise.add('mqm')
    Traceback (most recent call last):
    Exception: qcm already defined
    >>> exercise.add('qcm')
    Traceback (most recent call last):
    Exception: qcm already defined
    >>> c1 = qcm.add('good-choice', 'choice 1')
    >>> print etree.tostring(exercise.to_xml(), pretty_print=True)
    <Exercise>
      <question>the question</question>
      <qcm>
        <good-choice>choice 1</good-choice>
      </qcm>
    </Exercise>
    <BLANKLINE>


Accessing to the property
-------------------------

To access to the elements you just have use the python dict style: obj['my-prop'].

See the example below:

.. doctest::

    >>> from lxml import etree
    >>> import xmltool
    >>> from xmltool import dtd_parser
    >>> dtd_url = 'http://xmltool.lereskp.fr/examples/exercise.dtd'
    >>> dic = dtd_parser.parse(dtd_url=dtd_url)
    >>> exercise = dic['Exercise']()
    >>> question = exercise.add('question', 'the question')
    >>> comments = exercise.add('comments')
    >>> c1 = comments.add('good-comment', 'comment 1')
    >>> print exercise['question'].text
    the question
    >>> exercise['comments'][0]['good-comment'].text
    'comment 1'


Loading a XML file
-------------------

For this example we will load the following XML file:

.. include:: examples/movie.xml
    :code: xml

.. testsetup:: *

    import xmltool

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = xmltool.load(xml_filename)
    >>> print obj._attributes
    {'idmovie': 'M1'}
    >>> print obj #doctest: +ELLIPSIS
    <xmltool.dtd_parser.movie object at 0x...>
    >>> print obj['title'].text
    Full Metal Jacket
    >>> print obj['characters']['character'][0].text
    Matthew Modine
    >>> print obj['characters']['character'][0]._attributes
    {'idcharacter': 'C1'}


Writing a XML file
-------------------

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = xmltool.load(xml_filename)
    >>> obj['title'].text = 'My new title'
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
    >>> obj = xmltool.load(xml_filename, validate=False)
    >>> obj.write('examples/movie-1-updated.xml')

You can see that the comment tag is added automatically:

.. include:: examples/movie-1-updated.xml
    :code: xml
