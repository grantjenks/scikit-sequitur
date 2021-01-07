"""SciKit Sequitur Core

Python code adapted from a Javascript version written by Craig Nevill-Manning.

"""


class Symbol:
    """Symbol

    Initializes a new symbol. If it is non-terminal, increments the reference
    count of the corresponding rule.

    Tightly coupled with Rule. Not designed for extensibility.

    """

    # pylint: disable=protected-access,unidiomatic-typecheck

    def __init__(self, value, bigrams: dict):
        self.bigrams = bigrams
        self.next_symbol = None
        self.prev_symbol = None
        self.value = value
        if type(value) is Rule:
            rule: Rule = value
            rule.value += 1

    def append(self, value):
        """Insert a value after this one."""
        symbol = Symbol(value, self.bigrams)
        symbol.join(self.next_symbol)
        self.join(symbol)

    def join(self, right):
        """Link two symbols together, removing any old bigram from the hash
        table.

        """
        if self.next_symbol is not None:
            self._remove_bigram()

            # This is to deal with trigrams, where we only record the second
            # pair of the overlapping bigrams. When we delete the second pair,
            # we insert the first pair into the hash table so that we don't
            # forget about it.  e.g. abbbabcbb

            if (
                right.prev_symbol is not None
                and right.next_symbol is not None
                and right.value == right.prev_symbol.value
                and right.value == right.next_symbol.value
            ):
                self.bigrams[right._bigram()] = right

            if (
                self.prev_symbol is not None
                and self.next_symbol is not None
                and self.value == self.prev_symbol.value
                and self.value == self.next_symbol.value
            ):
                self.bigrams[self.prev_symbol._bigram()] = self.prev_symbol

        self.next_symbol = right
        right.prev_symbol = self

    def _remove_bigram(self):
        """Remove the bigram from the hash table."""
        bigram = self._bigram()
        if self.bigrams.get(bigram) is self:
            del self.bigrams[bigram]

    def check(self):
        """Check a new bigram. If it appears elsewhere, deal with it by calling
        match(), otherwise insert it into the hash table.

        """
        if type(self) is Rule or type(self.next_symbol) is Rule:
            return False
        bigram = self._bigram()
        match: Symbol = self.bigrams.get(bigram)
        if match is None:
            self.bigrams[bigram] = self
            return False
        if match.next_symbol is not self:
            self._process_match(match)
        return True

    def _process_match(self, match):
        """Process match by either reusing an existing rule or creating a new
        rule.

        Checks also for an underused rule.

        """
        if (
            type(match.prev_symbol) is Rule
            and type(match.next_symbol.next_symbol) is Rule
        ):
            # Reuse an existing rule.
            rule: Rule = match.prev_symbol
            self._substitute(rule)
        else:
            # Create a new rule.
            rule = Rule(0, self.bigrams)
            rule.join(rule)
            rule.prev_symbol.append(self.value)
            rule.prev_symbol.append(self.next_symbol.value)
            match._substitute(rule)
            self._substitute(rule)
            self.bigrams[rule.next_symbol._bigram()] = rule.next_symbol
        # Check for an underused rule
        if type(rule.next_symbol.value) is Rule:
            target_rule: Rule = rule.next_symbol.value
            if target_rule.value == 1:
                rule.next_symbol._expand()

    def _substitute(self, rule):
        """Substitute symbol and previous with given rule."""
        prev = self.prev_symbol
        prev.next_symbol._delete()
        prev.next_symbol._delete()
        prev.append(rule)
        if not prev.check():
            prev.next_symbol.check()

    def _delete(self):
        """Clean up for symbol deletion: removes hash table entry and decrement rule
        reference count.

        """
        self.prev_symbol.join(self.next_symbol)
        self._remove_bigram()
        if type(self.value) is Rule:
            rule: Rule = self.value
            rule.value -= 1

    def _expand(self):
        """This symbol is the last reference to its rule. It is deleted, and the
        contents of the rule _substituted in its place.

        """
        left = self.prev_symbol
        right = self.next_symbol
        value: Rule = self.value
        first = value.next_symbol
        last = value.prev_symbol
        self._remove_bigram()
        left.join(first)
        last.join(right)
        self.bigrams[last._bigram()] = last

    def _bigram(self):
        """Bigram tuple pair of self value and next symbol value."""
        return (self.value, self.next_symbol.value)


class Rule(Symbol):
    """Rule

    The rule node is the linked list of symbols that make up the rule. It
    points forward to the first symbol in the rule, and backwards to the last
    symbol in the rule. Its own value is a reference count recording the rule
    utility.

    Tightly coupled with Symbol. Not designed for extensibility.

    """


class Parser:
    """Parser for Sequitur parse trees."""

    def __init__(self):
        self._bigrams = {}
        rule = Rule(0, self._bigrams)
        rule.join(rule)
        self._tree = rule

    @property
    def tree(self):
        """Root of the parse tree."""
        return self._tree

    @property
    def bigrams(self):
        """Parser bigrams."""
        return self._bigrams

    def feed(self, iterable):
        """Feed iterable to the parser.

        Iterate items in iterable and build the parse tree.

        """
        tree: Rule = self._tree
        for value in iterable:
            tree.prev_symbol.append(value)
            tree.prev_symbol.prev_symbol.check()


if __name__ == "sksequitur.core":  # pragma: no cover
    try:
        from ._core import *  # noqa # pylint: disable=wildcard-import
    except ImportError:
        pass
