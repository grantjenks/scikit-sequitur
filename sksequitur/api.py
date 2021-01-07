"""SciKit Sequitur API

"""

from collections import Counter, defaultdict, deque
from itertools import chain, count

from .core import Parser, Rule


class Mark:
    """Mark token used to prevent bigram matches."""

    # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        name = type(self).__name__
        items = vars(self).items()
        args = ", ".join(f"{key}={value!r}" for key, value in items)
        return f"{name}({args})"

    def __str__(self):
        return "|"


class Production(int):
    """Production"""

    def __repr__(self):
        num = super().__repr__()
        return f"Production({num})"

    def __str__(self):
        return super().__repr__()


class Grammar(dict):
    """Convert start rule of parse tree to grammar."""

    # pylint: disable=unidiomatic-typecheck
    value_map = {
        " ": "_",
        "\n": chr(0x21B5),
        "\t": chr(0x21E5),
    }

    def __init__(self, tree):
        super().__init__()
        counter = count()
        rule_to_production = defaultdict(lambda: Production(next(counter)))
        self._tree = rule_to_production[tree]
        rules = deque([tree])
        while rules:
            rule = rules.popleft()
            production = rule_to_production[rule]
            if production in self:
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
            self[production] = values

    def lengths(self):
        """Return lengths of productions."""
        _lengths = {}

        def _visit(value):
            if type(value) is not Production:
                return 1
            if value in _lengths:
                return _lengths[value]
            length = sum(map(_visit, self[value]))
            _lengths[value] = length
            return length

        _lengths[self._tree] = _visit(self._tree)
        return Counter(_lengths)

    def counts(self):
        """Return counts of productions."""
        _counts = Counter(
            value
            for values in self.values()
            for value in values
            if type(value) is Production
        )
        _counts[self._tree] = 1
        return _counts

    def expansions(self):
        """Return expansions of productions."""
        _expansions = {}

        def _visit(value):
            if type(value) is not Production:
                yield value
                return
            if value in _expansions:
                yield from _expansions[value]
                return
            expansion = list(chain.from_iterable(map(_visit, self[value])))
            _expansions[value] = expansion
            yield from expansion

        _expansions[self._tree] = list(_visit(self._tree))
        return _expansions

    def expand(self, production):
        """Generator to expand production."""
        for value in self[production]:
            if type(value) is Production:
                yield from self.expand(value)
            else:
                yield value

    def __str__(self):
        expansions = self.expansions()
        value_map = self.value_map
        lines = []
        for production, values in sorted(self.items()):
            parts = [production, "->"]
            parts.extend(value_map.get(value, value) for value in values)
            prefix = " ".join(map(str, parts))
            if production == 0:
                lines.append(prefix)
                continue
            space = " " * max(1, 50 - len(prefix))
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
