Python SciKit Sequitur
======================

`SciKit Sequitur`_ is an Apache2 licensed Python module for inferring
compositional hierarchies from sequences.

Sequitur detects repetition and factors it out by forming rules in a
grammar. The rules can be composed of non-terminals, giving rise to a
hierarchy. It is useful for recognizing lexical structure in strings, and
excels at very long sequences. The Sequitur algorithm was originally developed
by Craig Nevill-Manning and Ian Witten.

.. code-block:: python

   >>> from sksequitur import parse
   >>> grammar = parse('hello hello')
   >>> print(grammar)
   0 -> 1 _ 1
   1 -> h e l l o                                    hello

`SciKit Sequitur`_ works on strings, lines, or any sequence of Python objects.


Features
--------

- Pure-Python
- Developed on Python 3.8
- Tested on CPython 3.6, 3.7, 3.8
- Tested using GitHub Actions on Linux, Mac, and Windows

.. image:: https://github.com/grantjenks/scikit-sequitur/workflows/integration/badge.svg
   :target: http://www.grantjenks.com/docs/sksequitur/


Quickstart
----------

Installing `scikit-sequitur`_ is simple with `pip <http://www.pip-installer.org/>`_::

  $ pip install scikit-sequitur

You can access documentation in the interpreter with Python's built-in help
function:

.. code-block:: python

   >>> import sksequitur
   >>> help(sksequitur)                    # doctest: +SKIP


Tutorial
--------

The `scikit-sequitur`_ module provides utilities for parsing sequences and
understanding grammars.

.. code-block:: python

   >>> from sksequitur import parse
   >>> print(parse('abcabc'))
   0 -> 1 1
   1 -> a b c                                        abc

The `parse` function is a shortcut for `Parser` and `Grammar` objects.

.. code-block:: python

   >>> from sksequitur import Parser
   >>> parser = Parser()

Feed works incrementally.

.. code-block:: python

   >>> parser.feed('ab')
   >>> parser.feed('cab')
   >>> parser.feed('c')

Parsers can be converted to Grammars.

.. code-block:: python

   >>> from sksequitur import Grammar
   >>> grammar = Grammar(parser.tree)
   >>> print(grammar)
   0 -> 1 1
   1 -> a b c                                        abc

Grammars are keyed by Productions.

.. code-block:: python

   >>> from sksequitur import Production
   >>> grammar[Production(0)]
   [Production(1), Production(1)]

Mark symbols can be used to store metadata about a sequence. The mark symbol is
printed as a pipe character "|".

.. code-block:: python

   >>> from sksequitur import Mark
   >>> mark = Mark()
   >>> mark
   Mark()
   >>> print(mark)
   |

Attributes can be added to mark symbols using keyword arguments.

.. code-block:: python

   >>> mark = Mark(kind='start', name='foo.py')
   >>> mark
   Mark(kind='start', name='foo.py')
   >>> mark.kind
   'start'

Mark symbols can not be made part of a rule.

.. code-block:: python

   >>> parser = Parser()
   >>> parser.feed('ab')
   >>> parser.feed([Mark()])
   >>> parser.feed('cab')
   >>> parser.feed([Mark()])
   >>> parser.feed('c')
   >>> grammar = Grammar(parser.tree)
   >>> print(grammar)
   0 -> 1 | c 1 | c
   1 -> a b                                          ab


Reference
---------

* `scikit-sequitur Documentation`_
* `scikit-sequitur at PyPI`_
* `scikit-sequitur at GitHub`_
* `scikit-sequitur Issue Tracker`_

.. _`scikit-sequitur Documentation`: http://www.grantjenks.com/docs/sksequitur/
.. _`scikit-sequitur at PyPI`: https://pypi.python.org/pypi/scikit-sequitur/
.. _`scikit-sequitur at GitHub`: https://github.com/grantjenks/scikit-sequitur/
.. _`scikit-sequitur Issue Tracker`: https://github.com/grantjenks/scikit-sequitur/issues/


License
-------

Copyright 2020 Grant Jenks

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy of the
License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.  See the License for the
specific language governing permissions and limitations under the License.


.. _`SciKit Sequitur`: http://www.grantjenks.com/docs/sksequitur/
.. _`scikit-sequitur`: http://www.grantjenks.com/docs/sksequitur/
