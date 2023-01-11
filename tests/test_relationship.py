import pytest
from basicco.type_checking import import_types

from estruttura._relationship import Relationship, Serializer, TypedSerializer
from estruttura.exceptions import (
    ConversionError,
    InvalidTypeError,
    SerializationError,
    ValidationError,
)


def test_validator():
    rel = Relationship(validator=float)
    rel.validate_value(3.14)
    rel.validate_value("3.14")
    assert rel.process_value(3.14) == 3.14
    assert rel.process_value("3.14") == "3.14"

    with pytest.raises(ValidationError):
        rel.process_value("abc")


def test_converter():
    rel = Relationship(converter=float)
    assert rel.convert_value(3.14) == 3.14
    assert rel.convert_value("3.14") == 3.14
    assert rel.process_value(3.14) == 3.14
    assert rel.process_value("3.14") == 3.14

    with pytest.raises(ConversionError):
        rel.process_value("abc")


def test_types():
    rel = Relationship(types=float)
    rel.check_value_type(3.14)
    assert rel.process_value(3.14) == 3.14

    with pytest.raises(InvalidTypeError):
        rel.check_value_type("3.14")

    with pytest.raises(InvalidTypeError):
        rel.process_value("3.14")


def test_subtypes():
    class MyFloat(float):
        pass

    rel = Relationship(types=float)
    rel.check_value_type(3.14)

    with pytest.raises(InvalidTypeError):
        rel.check_value_type(MyFloat(3.14))

    rel = Relationship(types=float, subtypes=True)
    rel.check_value_type(MyFloat(3.14))
    rel.check_value_type(3.14)


class Foo(object):
    def serialize(self):  # noqa
        return "FOO"

    @classmethod
    def deserialize(cls, serialized):
        assert serialized == "FOO"
        return cls()


class Bar(object):
    def serialize(self):  # noqa
        return "BAR"

    @classmethod
    def deserialize(cls, serialized):
        assert serialized == "BAR"
        return cls()


class Bad(object):
    pass


def test_typed_serializer():
    assert issubclass(TypedSerializer, Serializer)
    assert isinstance(Relationship().serializer, TypedSerializer)

    rel = Relationship(types=(Foo, Bar), subtypes=True)
    assert rel.serialize_value(Foo()) == {  # type: ignore
        "__class__": __name__ + "." + Foo.__name__,
        "__state__": "FOO",
    }
    assert rel.serialize_value(Bar()) == {  # type: ignore
        "__class__": __name__ + "." + Bar.__name__,
        "__state__": "BAR",
    }
    assert isinstance(rel.deserialize_value(rel.serialize_value(Foo())), Foo)  # type: ignore
    assert isinstance(rel.deserialize_value(rel.serialize_value(Bar())), Bar)  # type: ignore

    rel = Relationship(types=(Foo,), subtypes=False)
    assert rel.serialize_value(Foo()) == "FOO"
    assert isinstance(rel.deserialize_value(rel.serialize_value(Foo())), Foo)  # type: ignore

    rel = Relationship()
    assert rel.deserialize_value(rel.serialize_value(3)) == 3

    rel = Relationship(types=(int,))
    assert rel.deserialize_value(rel.serialize_value(3)) == 3

    rel = Relationship(types=(Bad,))
    with pytest.raises(SerializationError):
        rel.serialize_value(3)  # type: ignore
    with pytest.raises(SerializationError):
        rel.deserialize_value(3)  # type: ignore


def test_types_info():
    rel = Relationship(types=(int, "float", dict, list, set, Foo, Bar))
    assert rel.types_info.input_types == (int, "float", dict, list, set, Foo, Bar)
    assert rel.types_info.all_types == import_types((int, float, dict, list, set, Foo, Bar))
    assert rel.types_info.basic_types == import_types((int, float))
    assert rel.types_info.complex_types == import_types((dict, list, set, Foo, Bar))
    assert rel.types_info.mapping_types == import_types((dict,))
    assert rel.types_info.iterable_types == import_types((list, set))


if __name__ == "__main__":
    pytest.main()
