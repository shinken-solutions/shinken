.. _development/documentation:

======================
Shinken documentation
======================


About this documentation
=========================

This documentation uses `Python-sphinx`_, which itself uses `reStructuredText`_
syntax.

The guidelines below are loosely based on the `documentation-style-guide-sphinx`_ project and improve upon the converted content of the numerous of contributors to the shinken wiki.


Contribute by...
================

  * Removing all duplicate files / content from the source tree
  * Split the configuration parameters that are unused from the unimplemented ones
  * Remove the nagios and nagios-specific references (such as unused parameters) from the various pages
  * Clean up the gettingstarted / installations section
  * Fix the internal links on the "troubleshooting/troubleshooting-shinken" page
  * Dedicate a basic page on how to use the shinken.io packs
  * Shorten the directory names in the source directory for shorter links
  * Find or create the correct targets for:
    
    * the "configuringshinken/objectdefinitions#retention_notes" links, referenced multiple times by 
    
      * "configobjects/service"
      * "configobjects/host"
    
    * the "internal_metrics" links, or create the page based on http://www.shinken-monitoring.org/wiki/internal_metrics
    * the original "thebasics/cgis" links spread accross the documentation
  
  

Directory structure
===================

.. todo:: write about how links are tied to the directory structure


Filenames
=========

Use only lowercase alphanumeric characters and ``-`` (minus) symbol.

Suffix filenames with the ``.rst`` extension.


Indentation
===========

Indent with 2 spaces.

.. attention:: Except the ``toctree`` directive, it requires a 3 spaces indentation.


Blank lines
===========

Two blank lines before overlined sections, i.e. before H1 and H2.
See `Headings`_ for an example.

One blank line to separate directives.

.. code-block:: rst

  Some text before.

  .. note::

    Some note.
    On multiple lines.

Exception: directives can be written without blank lines if they are only one
line long.

.. code-block:: rst

  .. note:: A short note.


Headings
========

Use the following symbols to create headings:

  #. ``=`` with overline
  #. ``=``
  #. ``-``
  #. ``~``

If you use more then 4 levels, it's usually a sign that you should split the file into a subdirectory with multiple chapters.

As an example:

.. code-block:: rst

  ==================
  H1: document title
  ==================

  Introduction text.


  Sample H2
  =========

  Sample content.


  Another H2
  ==========

  
  Sample H3
  ---------

  
  Sample H4
  ~~~~~~~~~

  And some text.


There should be only one H1 in a document.

.. note:: See also `Sphinx's documentation about sections`_.


Code blocks
===========

Use the ``code-block`` directive **and** specify the programming language if appropriate. As
an example:

.. code-block:: rst

  .. code-block:: python

    import this


The **::** directive works for generic monospaced text as used in configuration files and shell commands

.. code-block:: rst

  ::
  
    define {
        parameter
    }


Links
=====

The definition of a target for a link is done by placing an anchor.

.. code-block:: rst

  .. _path-to-file/rst-filename:                        // placed on top of every file
  .. _path-to-file/index:                               // placed in every index file, in every subdirectory of the source directory
  .. _path-to-file/subdirectory/rst-filename:           // placed on top of a file in a subdirectory
  
  
  .. _path-to-file/rst-filename#anchor_on_the_page:     // placed as an in-page anchor to a title
  
  Anchor on the page
  ------------------

  
Links to the above anchors are made with the ``:ref:`` directive

.. code-block:: rst

  :ref:`this is a reference of the first anchor <path-to-file/rst-filename>`.
  :ref:`this is a reference of the last anchor <path-to-file/rst-filename#anchor_on_the_page>`
  
  
Note that we use underscores in the in-page anchors on titles, but use the ``-`` (minus) symbol in the rest of the links.
This has the advantage that a part of the file path can be copy-pasted when building links and only in-page anchors on titles need some extra care when making links.



References
==========

Optional when using a lot of references: use reference footnotes with the ``target-notes`` directive.
As an example:

.. code-block:: rst

  =============
  Some document
  =============

  Some text which includes links to `Example website`_ and many other links.

  `Example website`_ can be referenced multiple times.

  (... document content...)

  And at the end of the document...

  References
  ==========

  .. target-notes::

  .. _`Example website`: http://www.example.com/



Documenting code
=================

The documentation build process picks up your docstrings. See :ref:`the python docstring guide <development/programming-rules#python_docstring_guide>`.


References
==========

.. target-notes::

.. _`documentation-style-guide-sphinx`: http://documentation-style-guide-sphinx.readthedocs.org/en/latest/index.html
.. _`Python-sphinx`: http://sphinx.pocoo.org/
.. _`reStructuredText`: http://docutils.sourceforge.net/rst.html
.. _`rst2html`: http://docutils.sourceforge.net/docs/user/tools.html#rst2html-py
.. _`Github`: https://github.com
.. _`Read the docs`: http://readthedocs.org
.. _`Sphinx's documentation about sections`: http://sphinx.pocoo.org/rest.html#sections
