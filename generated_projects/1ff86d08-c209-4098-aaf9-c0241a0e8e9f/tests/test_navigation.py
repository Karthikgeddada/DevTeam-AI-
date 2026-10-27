import pytest

from core.navigation import navigation

def test_navigation_init():
    navigation.init()
    assert True

def test_navigation_go_back():
    navigation.goBack()
    assert True

def test_navigation_go_forward():
    navigation.goForward()
    assert True

def test_navigation_refresh():
    navigation.refresh()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])