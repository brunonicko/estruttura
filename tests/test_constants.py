import pytest

from estruttura.constants import (
    DEFAULT,
    DELETED,
    MISSING,
    DefaultType,
    DeletedType,
    MissingType,
)


def test_inheritance():
    assert isinstance(MISSING, MissingType)
    assert isinstance(DELETED, DeletedType)
    assert isinstance(DEFAULT, DefaultType)


if __name__ == "__main__":
    pytest.main()
