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
    __slots__ = ['bigrams', 'next_symbol', 'prev_symbol', 'value']

    def __init__(self, value, bigrams):
        self.bigrams = bigrams
        self.next_symbol = None
        self.prev_symbol = None
        self.value = value
        if value.__class__ is Rule:
            value.value += 1

    def insert_after(self, value):
        """Insert a value after this one."""
        symbol = Symbol(value, self.bigrams)
        symbol.join(self.next_symbol)
        self.join(symbol)

    def join(self, right):
        """Link two symbols together, removing any old bigram from the hash
        table.

        """
        if self.next_symbol:
            self.delete_bigram()

            # This is to deal with trigrams, where we only record the second
            # pair of the overlapping bigrams. When we delete the second pair,
            # we insert the first pair into the hash table so that we don't
            # forget about it.  e.g. abbbabcbb

            if (
                right.prev_symbol
                and right.next_symbol
                and right.value == right.prev_symbol.value
                and right.value == right.next_symbol.value
            ):
                self.bigrams[right.bigram()] = right

            if (
                self.prev_symbol
                and self.next_symbol
                and self.value == self.next_symbol.value
                and self.value == self.prev_symbol.value
            ):
                self.bigrams[self.bigram()] = self

        self.next_symbol = right
        right.prev_symbol = self

    def delete_bigram(self):
        """Remove the bigram from the hash table."""
        if self.__class__ is Rule or self.next_symbol.__class__ is Rule:
            return
        bigram = self.bigram()
        if self.bigrams.get(bigram) == self:
            del self.bigrams[bigram]

    def check(self):
        """Check a new bigram. If it appears elsewhere, deal with it by calling
        match(), otherwise insert it into the hash table.

        """
        if self.__class__ is Rule or self.next_symbol.__class__ is Rule:
            return False
        bigram = self.bigram()
        match = self.bigrams.get(bigram)
        if match is None:
            self.bigrams[bigram] = self
            return False
        if match.next_symbol != self:
            self.process_match(match)
        return True

    def process_match(self, match):
        """Process match by either reusing an existing rule or creating a new
        rule.

        Checks also for an underused rule.

        """
        if (
            match.prev_symbol.__class__ is Rule
            and match.next_symbol.next_symbol.__class__ is Rule
        ):
            # Reuse an existing rule.
            rule = match.prev_symbol
            self.substitute(rule)
        else:
            # Create a new rule.
            rule = Rule(self.bigrams)
            rule.prev_symbol.insert_after(self.value)
            rule.prev_symbol.insert_after(self.next_symbol.value)
            match.substitute(rule)
            self.substitute(rule)
            self.bigrams[rule.next_symbol.bigram()] = rule.next_symbol
        # Check for an underused rule
        if (
            rule.next_symbol.value.__class__ is Rule
            and rule.next_symbol.value.value == 1
        ):
            rule.next_symbol.expand()

    def substitute(self, rule):
        """Substitute symbol and previous with given rule."""
        prev = self.prev_symbol
        prev.next_symbol.delete()
        prev.next_symbol.delete()
        prev.insert_after(rule)
        if not prev.check():
            prev.next_symbol.check()

    def delete(self):
        """Clean up for symbol deletion: removes hash table entry and decrement rule
        reference count.

        """
        self.prev_symbol.join(self.next_symbol)
        if self.__class__ is not Rule:
            self.delete_bigram()
            if self.value.__class__ is Rule:
                self.value.value -= 1

    def expand(self):
        """This symbol is the last reference to its rule. It is deleted, and the
        contents of the rule substituted in its place.

        """
        left = self.prev_symbol
        right = self.next_symbol
        first = self.value.next_symbol
        last = self.value.prev_symbol
        bigram = self.bigram()
        if self.bigrams.get(bigram) == self:
            del self.bigrams[bigram]
        left.join(first)
        last.join(right)
        self.bigrams[last.bigram()] = last

    def bigram(self):
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
    __slots__ = []

    def __init__(self, bigrams=None):
        super().__init__(0, {} if bigrams is None else bigrams)
        self.join(self)


class Stop:
    __slots__ = []

    def __str__(self):
        return '|'


class Parser:
    """Parser for Sequitur parse trees.

    """

    def __init__(self):
        self._bigrams = {}
        self._tree = Rule(self._bigrams)

    @property
    def tree(self):
        """Root of the parse tree."""
        return self._tree

    @property
    def bigrams(self):
        return self._bigrams

    def feed(self, iterable):
        """Feed iterable to the parser.

        Iterate items in iterable and build the parse tree.

        """
        tree = self._tree
        for value in iterable:
            tree.prev_symbol.insert_after(value)
            tree.prev_symbol.prev_symbol.check()

    def stop(self):
        """Add stop token to the parser.

        """
        tree = self._tree
        stop = Stop()
        tree.prev_symbol.insert_after(stop)
        tree.prev_symbol.check()


class Production(int):
    """Production

    """
    __slots__ = []


class Grammar:
    """Initialize a grammar from a start rule.

    """
    value_map = {
        ' ': '_',
        '\n': chr(0x21B5),
        '\t': chr(0x21E5),
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
            while not symbol.__class__ is Rule:
                value = symbol.value
                if value.__class__ is Rule:
                    rules.append(value)
                    value = rule_to_production[value]
                values.append(value)
                symbol = symbol.next_symbol
            productions[production] = values

    def build_expansions(self):
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
            parts = [production, '->']
            parts.extend(value_map.get(value, value) for value in values)
            prefix = ' '.join(map(str, parts))
            if production == 0:
                lines.append(prefix)
                continue
            space = ' ' * (50 - len(prefix) if len(prefix) < 50 else 1)
            expansion = expansions[production]
            parts = (value_map.get(value, value) for value in expansion)
            suffix = ''.join(map(str, parts))
            triple = prefix, space, suffix
            line = ''.join(triple)
            lines.append(line)
        return '\n'.join(lines)


def parse(iterable):
    """Parse iterable and return grammar."""
    parser = Parser()
    parser.feed(iterable)
    grammar = Grammar(parser.tree)
    return grammar
