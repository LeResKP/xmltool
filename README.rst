xmltool
=========

xmltool is a python package to manipulate XML files. It's very useful to update some XML files with the python syntax without using the DOM.
The main goal of this package was to create a HTML form to edit and create a XML file. The form generation is based on a dtd file.
`Read the documentation <http://xmltool.lereskp.fr>`_


Changelog
=========

O.3.6.2:
    * Support to have comment inside a TextElement
    * Improve HTML rendering
    * Bug fix: make numdict_to_list works when we have more than 9 elements

O.3.6.1:
    * Be able to skip attributes and comments when we load object

O.3.6:
    * Add functions to update existing object with data from other one
    * Some cleanup and fixes

O.3.5:
    * Use grunt to manage the webmedia
    * Use bootstrap to make the HTML rendering
    * javascript performance
    * xpath support
    * Only use the dict style to access elements
    * Deprecate some attributes

O.3.4:
    * Make xmltool works with old version of lxml
    * Be able to pass attributes to the HTML form

O.3.3:
    * Fix missing require

O.3.2:
    * Better support for local dtd. It can a relative path from the XML filename.
    * Bug fix: the EMPTY tags are support correctly!

O.3.1:
    * Render the text element as HTML format when exporting in XML (no autoclose tag)
    * Bug fix: make sure we add empty text element in the HTML form

O.3:
    * Rewrite the core of the code
    * Better performance to generate the HTML
    * Bug fix

O.2:
    * Update the project architecture
    * Be able to access to the element properties like a dict
    * Add functions to easily update or create XML file
    * Fix missing README file in the package

O.1:
    * Initial version: package to manipulate XML file and create HTML forms.



Build Status
------------

.. |master| image:: https://secure.travis-ci.org/LeResKP/xmltool.png?branch=master
   :alt: Build Status - master branch
   :target: https://travis-ci.org/#!/LeResKP/xmltool

.. |develop| image:: https://secure.travis-ci.org/LeResKP/xmltool.png?branch=develop
   :alt: Build Status - develop branch
   :target: https://travis-ci.org/#!/LeResKP/xmltool

+----------+-----------+
| Branch   | Status    |
+==========+===========+
| master   | |master|  |
+----------+-----------+
| develop  | |develop| |
+----------+-----------+
