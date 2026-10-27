import pytest

from ui.navbar import navbar
from ui.addressbar import addressbar
from ui.tabbar import tabbar

def test_navbar_init():
    navbar.init()
    assert True

def test_addressbar_init():
    addressbar.init()
    assert True

def test_tabbar_init():
    tabbar.init()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])