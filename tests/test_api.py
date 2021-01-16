from sksequitur.api import Production


def test_repr():
    assert repr(Production(0)) == 'Production(0)'
