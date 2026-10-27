import pytest

from core.bookmarking import bookmarking

def test_bookmarking_init():
    bookmarking.init()
    assert True

def test_bookmarking_bookmark():
    bookmarking.bookmark()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])