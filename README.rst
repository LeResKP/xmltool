xml-tools
=========

xmltool is a python package to manipulate XML files. It's very useful to update some XML files with the python syntax without using the DOM.
The main goal of this package was to create a HTML form to edit and create a XML file. The form generation is based on a dtd file.
`Read the documentation <http://xml-tools.lereskp.fr>`_


Changelog
=========

O.3:
    * Rewrite the core of the code
    * Better performance to generate the HTML
    * Fix bug

O.2:
    * Update the project architecture
    * Be able to access to the element properties like a dict
    * Add functions to easily update or create XML file
    * Fix missing README file in the package

O.1:
    * Initial version: package to manipulate XML file and create HTML forms.



Build Status
------------

.. |master| image:: https://secure.travis-ci.org/LeResKP/xml-tools.png?branch=master
   :alt: Build Status - master branch
   :target: https://travis-ci.org/#!/LeResKP/xml-tools

.. |develop| image:: https://secure.travis-ci.org/LeResKP/xml-tools.png?branch=develop
   :alt: Build Status - develop branch
   :target: https://travis-ci.org/#!/LeResKP/xml-tools

+----------+-----------+
| Branch   | Status    |
+==========+===========+
| master   | |master|  |
+----------+-----------+
| develop  | |develop| |
+----------+-----------+
