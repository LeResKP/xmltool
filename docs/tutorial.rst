########
Tutorial
########


We will create a new XML file from scratch with 2 movies.


.. doctest::

    >>> import xmltool
    >>> dtd_url = 'examples/movies.dtd'
    >>> movies = xmltool.create('movies', dtd_url=dtd_url)
    >>> movie_fmj = movies.add('movie')
    >>> t = movie_fmj.add('title', 'Full Metal Jacket')
    >>> r = movie_fmj.add('realisator', 'Stanley Kubrick')
    >>> characters = movie_fmj.add('characters')
    >>> c1 = characters.add('character', 'Matthew Modine')
    >>> c2 = characters.add('character', 'Vincent D\'Onofrio')
    >>> print movies
    <movies>
      <movie>
        <title>Full Metal Jacket</title>
        <realisator>Stanley Kubrick</realisator>
        <characters>
          <character>Matthew Modine</character>
          <character>Vincent D'Onofrio</character>
        </characters>
      </movie>
    </movies>
    <BLANKLINE>
    >>> movie_tit = movies.add('movie')
    >>> t = movie_tit.add('title', 'Titanic')
    >>> r = movie_tit.add('realisator', 'Cameron James')
    >>> characters = movie_tit.add('characters')
    >>> c1 = characters.add('character', 'Leonardo DiCaprio')
    >>> c2 = characters.add('character', 'Kate Winslet')
    >>> print movies
    <movies>
      <movie>
        <title>Full Metal Jacket</title>
        <realisator>Stanley Kubrick</realisator>
        <characters>
          <character>Matthew Modine</character>
          <character>Vincent D'Onofrio</character>
        </characters>
      </movie>
      <movie>
        <title>Titanic</title>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
      </movie>
    </movies>
    <BLANKLINE>
    >>> movies.write('examples/tutorial1.xml')


Insert element in list
----------------------


We will add a new movie after "Full Metal Jacket" so we have to pass ``index=1``. If you want to add the movie at the last place don't pass index.

.. doctest::

    >>> import xmltool
    >>> movies = xmltool.load('examples/tutorial1.xml')
    >>> movie = movies.add('movie', index=1)
    >>> print movies
    <movies>
      <movie>
        <title>Full Metal Jacket</title>
        <realisator>Stanley Kubrick</realisator>
        <characters>
          <character>Matthew Modine</character>
          <character>Vincent D'Onofrio</character>
        </characters>
      </movie>
      <movie>
        <title></title>
        <realisator></realisator>
        <characters>
          <character></character>
        </characters>
      </movie>
      <movie>
        <title>Titanic</title>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
      </movie>
    </movies>
    <BLANKLINE>


Delete element
--------------


We will delete the movie "Full Metal Jacket" which is the first of the list.

.. doctest::

    >>> import xmltool
    >>> movies = xmltool.load('examples/tutorial1.xml')
    >>> movies['movie'][0].delete()
    >>> print movies
    <movies>
      <movie>
        <title>Titanic</title>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
      </movie>
    </movies>
    <BLANKLINE>
    >>> movies.write()


Choice element
--------------


Add and delete choice element.


.. doctest::

    >>> import xmltool
    >>> movies = xmltool.load('examples/tutorial1.xml')
    >>> movie = movies['movie'][0]
    >>> c1 = movie.add('good', 'Good movie')
    >>> print movies
    <movies>
      <movie>
        <title>Titanic</title>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
        <good>Good movie</good>
      </movie>
    </movies>
    <BLANKLINE>
    >>> print movie['good'].text
    Good movie
    >>> movie.add('bad')
    Traceback (most recent call last):
    Exception: good is defined so you can't add bad
    >>> movie['good'].delete()
    >>> bad = movie.add('bad')
    >>> print movies
    <movies>
      <movie>
        <title>Titanic</title>
        <realisator>Cameron James</realisator>
        <characters>
          <character>Leonardo DiCaprio</character>
          <character>Kate Winslet</character>
        </characters>
        <bad></bad>
      </movie>
    </movies>
    <BLANKLINE>


List choice element
-------------------


We will add a good-comment and a bad-comment

.. doctest::

    >>> import xmltool
    >>> movies = xmltool.load('examples/tutorial1.xml')
    >>> movie = movies['movie'][0]
    >>> c1 = movie.add('good-comment', 'My comment 1')
    >>> c2 = movie.add('bad-comment', 'My comment 2')
    >>> print movies
    <movies>
      <movie>
        <title>Titanic</title>
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
    >>> movies.write()


Since {good,bad}-comment is a choice list it's a bit different to access, a property named list__tag1_tag2_... is automatically create. For this example it's list__good-comment_bad-comment.


.. doctest::

    >>> import xmltool
    >>> movies = xmltool.load('examples/tutorial1.xml')
    >>> comments = movies['movie'][0]['list__good-comment_bad-comment']
    >>> print comments[0].text
    My comment 1
    >>> print comments[1].text
    My comment 2


