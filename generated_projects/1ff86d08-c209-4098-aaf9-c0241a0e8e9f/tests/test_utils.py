import pytest

from utils.utils import utils

def test_utils_init():
    utils.init()
    assert True

def test_utils_helper():
    utils.helper()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])