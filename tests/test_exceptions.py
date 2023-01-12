import pytest

from estruttura.exceptions import ConversionError, InvalidTypeError, ProcessingError, ValidationError


def test_inheritance():
    assert issubclass(ConversionError, ProcessingError)
    assert issubclass(ValidationError, ProcessingError)
    assert issubclass(InvalidTypeError, ProcessingError)


if __name__ == "__main__":
    pytest.main()
