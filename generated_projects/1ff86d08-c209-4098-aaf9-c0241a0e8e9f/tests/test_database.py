import pytest

from database.schema import schema

def test_schema_init():
    schema.init()
    assert True

def test_schema_create():
    schema.create()
    assert True

if __name__ == '__main__':
    pytest.main(["-v", "tests"])