###############
Getting started
###############


For the following examples will use this dtd content:


.. include:: examples/movies.dtd
    :code: dtd


Creating a XML file
===================

To create a XML we just need to call the method ``create`` like in the following example:


.. We need to create a copy to be sure we will display the good XML since movies.xml will be updated later.
.. testsetup::

    import xmltool
    dtd_url = 'examples/movies.dtd'
    movies = xmltool.create('movies', dtd_url=dtd_url)
    movies.write('examples/movies-duplicated.xml')


.. doctest::

    >>> import xmltool
    >>> dtd_url = 'examples/movies.dtd'
    >>> movies = xmltool.create('movies', dtd_url=dtd_url)
    >>> print movies
    <movies/>
    <BLANKLINE>
    >>> movies.write('examples/movies.xml')


You can see the content of the generated file and note that the required tags have been added automatically to make a valid XML file.

.. include:: examples/movies-duplicated.xml
    :code: xml


Loading a XML file
===================

For this example we load the file previously created:

.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> print movies
    <movies/>
    <BLANKLINE>


Updating a XML file
===================

Now we will see that updating an XML is very easy:


.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> print movies
    <movies/>
    <BLANKLINE>
    >>> movie = movies.add('movie')
    >>> title = movie.add('title', 'Full Metal Jacket')
    >>> print title
    <title>Full Metal Jacket</title>
    <BLANKLINE>
    >>> print movies
    <movies>
      <movie>
        <title>Full Metal Jacket</title>
        <realisator></realisator>
        <characters>
          <character></character>
        </characters>
      </movie>
    </movies>
    <BLANKLINE>
    >>> movies.write()


Accessing
=========


To access a property of the XML object you have to use the list and dictionnary syntax.


.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> # As you can see in the dtd, movies has only one child movie
    >>> # which is a repeated element.
    >>> # Here is the syntax to get the first movie
    >>> print movies['movie'][0]
    <movie>
      <title>Full Metal Jacket</title>
      <realisator></realisator>
      <characters>
        <character></character>
      </characters>
    </movie>
    <BLANKLINE>
    >>> # You have the text property to access to the value of a tag
    >>> print movies['movie'][0]['title'].text
    Full Metal Jacket


To check if a XML property exists you can use if ... in ... or .get():

.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> movie1 = movies['movie'][0]
    >>> print 'date' in movie1
    False
    >>> print movie1.get('date')
    None

There is also a method to get or add element

.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> movie1 = movies['movie'][0]
    >>> # Long version
    >>> if 'date' not in movie1:
    ...     date = movie1.add('date')
    >>> # Short version
    >>> date = movie1.get_or_add('date')


We can also access to the attributes

.. doctest::

    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> movie1 = movies['movie'][0]
    >>> movie1.add_attribute('idmovie', 'myid')
    >>> print movie1
    <movie idmovie="myid">
      <title>Full Metal Jacket</title>
      <realisator></realisator>
      <characters>
        <character></character>
      </characters>
    </movie>
    <BLANKLINE>
    >>> print movie1.attributes['idmovie']
    myid


Traversing
==========

To find all elements from a tagname use ``findall``

.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>> # Add 2 new movies to improve this example
    >>> for i in range(2):
    ...     movie = movies.add('movie')
    ...     title = movie.add('title', 'Title %i' % i)
    >>> titles = movies.findall('title')
    >>> titles_str = [t.text for t in titles]
    >>> print titles_str
    ['Full Metal Jacket', 'Title 0', 'Title 1']


You can also go through all the elements by using ``walk``

.. doctest::

    >>> import xmltool
    >>> filename = 'examples/movies.xml'
    >>> movies = xmltool.load(filename)
    >>>
    >>> tagnames = [elt.tagname for elt in movies.walk()]
    >>> print tagnames
    ['movie', 'title', 'realisator', 'characters', 'character']
