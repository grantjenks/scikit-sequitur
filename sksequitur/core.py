"""SciKit Sequitur Core

"""

from collections import defaultdict, deque
from itertools import chain, count


class Symbol:
    """Symbol

    Initializes a new symbol. If it is non-terminal, increments the reference
    count of the corresponding rule.

    Tightly coupled with Rule.

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
                and self.value == self.next_symbol.value
                and self.value == self.prev_symbol.value
            ):
                self.bigrams[self._bigram()] = self

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

    The guard node is the linked list of symbols that make up the rule. It
    points forward to the first symbol in the rule, and backwards to the last
    symbol in the rule. Its own value points to the rule data structure, so
    that symbols can find out which rule they're in.

    Tightly coupled with Symbol.

    """


class Stop:
    """Stop token used to prevent bigram matches."""

    # pylint: disable=too-few-public-methods

    __slots__: list = []

    def __str__(self):
        return "|"


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

    def stop(self):
        """Add stop token to the parser."""
        tree: Rule = self._tree
        stop = Stop()
        tree.prev_symbol.append(stop)
        tree.prev_symbol.prev_symbol.check()


class Production(int):
    """Production"""

    __slots__: list = []


class Grammar:
    """Initialize a grammar from a start rule."""

    # pylint: disable=unidiomatic-typecheck

    value_map = {
        " ": "_",
        "\n": chr(0x21B5),
        "\t": chr(0x21E5),
    }

    def __init__(self, tree):
        self._productions = productions = {}
        self._expansions = {}
        counter = count()
        rule_to_production = defaultdict(lambda: Production(next(counter)))
        self._tree = rule_to_production[tree]
        rules = deque([tree])
        while rules:
            rule = rules.popleft()
            production = rule_to_production[rule]
            if production in productions:
                continue  # Already visited.
            symbol = rule.next_symbol
            values = []
            while type(symbol) is not Rule:
                value = symbol.value
                if type(value) is Rule:
                    rules.append(value)
                    value = rule_to_production[value]
                values.append(value)
                symbol = symbol.next_symbol
            productions[production] = values

    def build_expansions(self):
        """Build expansions for each production."""
        productions = self._productions
        expansions = self._expansions

        def _visit(production):
            if not isinstance(production, Production):
                return [production]
            if production in expansions:
                return expansions[production]
            iterator = map(_visit, productions[production])
            expansion = list(chain.from_iterable(iterator))
            expansions[production] = expansion
            return expansion

        expansions.clear()
        tree = self._tree
        expansions[tree] = _visit(tree)

    def __str__(self):
        self.build_expansions()
        expansions = self._expansions
        value_map = self.value_map
        lines = []
        for production, values in sorted(self._productions.items()):
            parts = [production, "->"]
            parts.extend(value_map.get(value, value) for value in values)
            prefix = " ".join(map(str, parts))
            if production == 0:
                lines.append(prefix)
                continue
            space = " " * (50 - len(prefix) if len(prefix) < 50 else 1)
            expansion = expansions[production]
            parts = (value_map.get(value, value) for value in expansion)
            suffix = "".join(map(str, parts))
            triple = prefix, space, suffix
            line = "".join(triple)
            lines.append(line)
        return "\n".join(lines)


def parse(iterable):
    """Parse iterable and return grammar."""
    parser = Parser()
    parser.feed(iterable)
    grammar = Grammar(parser.tree)
    return grammar
