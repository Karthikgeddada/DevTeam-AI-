import pytest

from extensions.extension import extension

def test_extension_init():
    extension.init()
    assert True

def test_extension_load():
    extension.load()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])