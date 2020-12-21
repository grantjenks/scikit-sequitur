"""Sequitur

Sequitur is a method for inferring compositional hierarchies from strings. It
detects repetition and factors it out of the string by forming rules in a
grammar. The rules can be composed of non-terminals, giving rise to a
hierarchy. It is useful for recognizing lexical structure in strings, and
excels at very long sequences.

The algorithm was developed by:
    Craig Nevill-Manning, Google
    Ian Witten, University of Waikato, New Zealand

More details are available online at http://www.sequitur.info/

"""

from .core import Printer, Rule, parse  # noqa: F401

__title__ = "sksequitur"
__version__ = "0.0.2"
