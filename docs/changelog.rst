Changelog
=========

1.1.0:
   * Drop python 2 support
   * Remove HTML generation
   * Remove JS/CSS stuff

1.0.0:
   * python 3 support

0.5.2:
   * Close correctly temporary file

0.5.1:
   * Fix dtd cache

0.5:
   * Add CDATA support
   * Improve dtd validation

O.4:
    * Rewrite javascript and add unittest
    * Cleanup python code
    * Remove deprecated functions

O.3.7:
    * Cache to get the dtd content
    * CKEditor render

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
