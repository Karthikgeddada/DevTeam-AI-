import pytest

from core.search import search

def test_search_init():
    search.init()
    assert True

def test_search_search_website():
    search.searchWebsite()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])