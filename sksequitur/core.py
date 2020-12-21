"""SciKit Sequitur Core

"""


class Symbol:
    """Symbol

    Initializes a new symbol. If it is non-terminal, increments the reference
    count of the corresponding rule.

    Tightly coupled with Rule.

    """

    def __init__(self, value, bigrams):
        self.bigrams = bigrams
        self.next_symbol = None
        self.prev_symbol = None
        self.token = None
        self.rule = None

        if type(value) is Rule:  # pylint: disable=unidiomatic-typecheck
            self.rule = value
            self.rule.refcount += 1
        else:
            self.token = value
            assert self.token, "Token values must be truthy"

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

    def delete(self):
        """Clean up for symbol deletion: removes hash table entry and decrement rule
        reference count.

        """
        self.prev_symbol.join(self.next_symbol)
        if not self.is_guard():
            self.delete_bigram()
            if self.rule:
                self.rule.refcount -= 1

    def delete_bigram(self):
        """Remove the bigram from the hash table."""
        if self.is_guard() or self.next_symbol.is_guard():
            return
        if self.bigrams.get(self.bigram()) == self:
            del self.bigrams[self.bigram()]

    def insert_after(self, value):
        """Insert a value after this one."""
        symbol = Symbol(value, self.bigrams)
        symbol.join(self.next_symbol)
        self.join(symbol)

    def is_guard(self):
        """Return true if this is the guard node marking the beginning and end of a
        rule.

        """
        return self.rule and self.rule.next_symbol.prev_symbol == self

    def check(self):
        """Check a new bigram. If it appears elsewhere, deal with it by calling
        match(), otherwise insert it into the hash table.

        """
        if self.is_guard() or self.next_symbol.is_guard():
            return False
        match = self.bigrams.get(self.bigram())
        if not match:
            self.bigrams[self.bigram()] = self
            return False
        if match.next_symbol != self:
            self.process_match(match)
        return True

    def expand(self):
        """This symbol is the last reference to its rule. It is deleted, and the
        contents of the rule substituted in its place.

        """
        left = self.prev_symbol
        right = self.next_symbol
        first = self.rule.next_symbol
        last = self.rule.prev_symbol
        if self.bigrams.get(self.bigram()) == self:
            del self.bigrams[self.bigram()]
        left.join(first)
        last.join(right)
        self.bigrams[last.bigram()] = last

    def substitute(self, rule):
        """Substitute symbol and previous with given rule."""
        prev = self.prev_symbol
        prev.next_symbol.delete()
        prev.next_symbol.delete()
        prev.insert_after(rule)
        if not prev.check():
            prev.next_symbol.check()

    def process_match(self, match):
        """Process match by either reusing an existing rule or creating a new
        rule.

        Checks also for an underused rule.

        """
        if (
            match.prev_symbol.is_guard()
            and match.next_symbol.next_symbol.is_guard()
        ):
            # Reuse an existing rule.
            rule = match.prev_symbol.rule
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
        if rule.next_symbol.rule and rule.next_symbol.rule.refcount == 1:
            rule.next_symbol.expand()

    @property
    def value(self):
        """Return value of symbol.

        The "rule" attribute is None for Symbol instances and set for Rule
        instances.

        """
        return self.rule or self.token

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

    def __init__(self, bigrams=None):
        self.refcount = -1
        super().__init__(self, {} if bigrams is None else bigrams)
        assert self.refcount == 0, "Symbol should increment refcount"
        self.join(self)

    def parse(self, iterable):
        """Parse iterable by repeatedly inserting elements at the end of the
        rule.

        """
        for value in iterable:
            self.prev_symbol.insert_after(value)
            self.prev_symbol.prev_symbol.check()


class Printer:
    """Printer for Rule-based grammars."""

    def __init__(self):
        self.rule_set = []
        self.output_array = []
        self.line_length = 0
        self.numbers = {}

    def print_rule(self, rule):
        """Visit rule."""
        symbol = rule.next_symbol
        while not symbol.is_guard():
            if symbol.rule:
                if (
                    self.rule_set[self.numbers.get(symbol.rule, 0)]
                    == symbol.rule
                ):
                    rule_number = self.numbers[symbol.rule]
                else:
                    rule_number = len(self.rule_set)
                    self.numbers[symbol.rule] = rule_number
                    self.rule_set.append(symbol.rule)
                self.output_array.append(str(rule_number) + " ")
                self.line_length += len(str(rule_number) + " ")
            else:
                self.output_array.append(self.print_token(symbol.value))
                self.output_array.append(" ")
                self.line_length += 2
            symbol = symbol.next_symbol

    @staticmethod
    def print_token(value):
        """Print token."""
        value = str(value)
        if value == " ":
            return "_"
        if value == "\n":
            return chr(0x21B5)
        if value == "\t":
            return chr(8677)
        if value in ("\\", "(", ")", "_") or value.isdigit():
            return value
        return value

    def print_rule_expansion(self, rule):
        """Visit rule and add expandsion."""
        symbol = rule.next_symbol
        while not symbol.is_guard():
            if symbol.rule:
                self.print_rule_expansion(symbol.rule)
            else:
                self.output_array.append(self.print_token(symbol.value))
            symbol = symbol.next_symbol

    def print_grammar(self, start):
        """Print grammar."""
        self.rule_set.append(start)
        i = 0

        while i < len(self.rule_set):
            self.output_array.append(f"{i} → ")
            self.line_length = len(f"{i}    ")
            self.print_rule(self.rule_set[i])

            if i > 0:
                self.output_array.append(" " * (50 - self.line_length))
                self.print_rule_expansion(self.rule_set[i])

            self.output_array.append("\n")

            i += 1

        result = "".join(self.output_array)
        lines = result.splitlines()
        lines = [line.rstrip() for line in lines]
        return "\n".join(lines) + "\n"


def parse(iterable):
    """Parse iterable and return grammar."""
    start = Rule()
    start.parse(iterable)
    printer = Printer()
    result = printer.print_grammar(start)
    return result
