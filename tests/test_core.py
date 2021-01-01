import pathlib

from sksequitur import parse

module_dir = pathlib.Path(__file__).parent


def test_hello2():
    iterable = "hello hello\n"
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 _ 1 ↵
1 -> h e l l o                                    hello\
"""
    assert str(grammar) == result


def test_abcabdabcabd():
    iterable = "abcabdabcabd"
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 1
1 -> 2 c 2 d                                      abcabd
2 -> a b                                          ab\
"""
    assert str(grammar) == result


def test_pease_porridge():
    iterable = """\
pease porridge hot,
pease porridge cold,
pease porridge in the pot,
nine days old.

some like it hot,
some like it cold,
some like it in the pot,
nine days old.\
"""
    grammar = parse(iterable)
    print(grammar)
    result = """\
0 -> 1 2 3 4 3 5 ↵ ↵ 6 2 7 4 7 5
1 -> p e a s 8 r r i d g 9                        pease_porridge_
2 -> h o t                                        hot
3 -> 10 1                                         ,↵pease_porridge_
4 -> c 11                                         cold
5 -> 12 _ t h 8 t 10 n 12 9 d a y s _ 11 .        in_the_pot,↵nine_days_old.
6 -> s o m 9 l i k 9 i t _                        some_like_it_
7 -> 10 6                                         ,↵some_like_it_
8 -> 9 p o                                        e_po
9 -> e _                                          e_
10 -> , ↵                                         ,↵
11 -> o l d                                       old
12 -> i n                                         in\
"""

    # from sksequitur.core import Parser, Printer
    # parser = Parser()
    # parser.feed(iterable)
    # printer = Printer()
    # printer_result = printer.print_grammar(parser.tree)
    # assert printer_result == result


    assert str(grammar) == result


def test_genesis():
    with open(module_dir / "genesis_input.txt") as reader:
        iterable = reader.read()
    grammar = parse(iterable)
    # print(grammar)
    with open(module_dir / "genesis_result.txt") as reader:
        result = reader.read()
    assert result.endswith('\n')
    assert str(grammar) == result[:-1]


def test_green_eggs_ham():
    with open(module_dir / "iamsam_input.txt") as reader:
        iterable = reader.read()
    grammar = parse(iterable)
    # print(grammar)
    with open(module_dir / "iamsam_result.txt") as reader:
        result = reader.read()
    assert result.endswith('\n')
    assert str(grammar) == result[:-1]


def test_nums():
    iterable = [1, 2, 3, 4, 1, 2, 3, 5, 1, 2, 3]
    grammar = parse(iterable)
    print(grammar)
    result = """\
0 -> 1 4 1 5 1
1 -> 1 2 3                                        123\
"""
    assert str(grammar) == result
