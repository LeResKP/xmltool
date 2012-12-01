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

    >>> import xmltools
    >>> gen = xmltools.Generator(dtd_url='http://xml-tools.lereskp.fr/examples/movie.dtd')
    >>> movie = gen.create_obj('movie')
    >>> title = movie.create('title', 'Movie title')
    >>> print title.value
    Movie title
    >>> realisator = movie.create('realisator', 'realisator name')
    >>> characters = movie.create('characters')
    >>> character_list = characters.create('character')
    >>> print character_list
    []
    >>> c1 = character_list.add('character 1')
    >>> c2 = character_list.add('character 2')
    >>> print movie.to_xml()
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

    >>> import xmltools
    >>> gen = xmltools.Generator(dtd_url='http://xml-tools.lereskp.fr/examples/exercise.dtd')
    >>> exercise = gen.create_obj('Exercise')
    >>> question = exercise.create('question', 'the question')
    >>> qcm_list = exercise.create('qcm')
    >>> print qcm_list
    []
    >>> # Now we can't add a mqm since a qcm exists
    >>> exercise.create('mqm')
    Traceback (most recent call last):
    Exception: You can't add a mqm since it already contains a qcm
    >>> qcm1 = qcm_list.add()
    >>> c1 = qcm1.create('good-choice', 'choice 1')
    >>> print exercise.to_xml()
    <Exercise>
      <question>the question</question>
      <qcm>
        <good-choice>choice 1</good-choice>
      </qcm>
    </Exercise>
    <BLANKLINE>


Accessing to the property
-------------------------

There is two ways to access to a property:
    * object style: obj.my_prop
    * dict style: obj['my_prop']. The dict style is very useful to access to the properties containing a dash.

See the example below:

.. doctest::

    >>> import xmltools
    >>> gen = xmltools.Generator(dtd_url='http://xml-tools.lereskp.fr/examples/exercise.dtd')
    >>> exercise = gen.create_obj('Exercise')
    >>> question = exercise.create('question', 'the question')
    >>> qcm_list = exercise.create('qcm')
    >>> qcm1 = qcm_list.add()
    >>> c1 = qcm1.create('good-choice', 'choice 1')
    >>> print exercise.question.value
    the question
    >>> exercise.qcm == exercise['qcm']
    True
    >>> exercise['qcm'][0]['good-choice'].value
    'choice 1'


Loading a XML file
-------------------

For this example we will load the following XML file:

.. include:: examples/movie.xml
    :code: xml

.. testsetup:: *

    import xmltools

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = xmltools.load(xml_filename)
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


Writing a XML file
-------------------

.. doctest::

    >>> xml_filename = 'examples/movie.xml'
    >>> obj = xmltools.load(xml_filename)
    >>> obj.title.value = 'My new title'
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
    >>> obj = xmltools.load(xml_filename, validate_xml=False)
    >>> obj.write('examples/movie-1-updated.xml')

You can see that the comment tag is added automatically:

.. include:: examples/movie-1-updated.xml
    :code: xml
