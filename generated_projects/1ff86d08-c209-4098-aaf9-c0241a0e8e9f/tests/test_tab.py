import pytest

from core.tab import tab

def test_tab_init():
    tab.init()
    assert True

def test_tab_open():
    tab.open()
    assert True

def test_tab_close():
    tab.close()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])