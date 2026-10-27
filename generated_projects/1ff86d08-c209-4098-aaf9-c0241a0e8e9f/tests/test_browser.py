import pytest

from core.browser import browser

def test_browser_init():
    browser.init()
    assert True

def test_browser_open_tab():
    browser.openTab()
    assert True

def test_browser_close_tab():
    browser.closeTab()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])