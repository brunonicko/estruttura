import pytest

from estruttura._attribute import Attribute
from estruttura._dict import DictStructure
from estruttura._helpers import attribute, dict_attribute, dict_cls, list_attribute, list_cls, set_attribute, set_cls
from estruttura._list import ListStructure
from estruttura._relationship import Relationship
from estruttura._set import SetStructure
from estruttura.examples import ImmutableClass

_KEY_RELATIONSHIP_KWARGS = dict(converter=str, validator=str, types=(str,), subtypes=True)
_RELATIONSHIP_KWARGS = dict(converter=float, validator=float, types=(float,), subtypes=True)


def test_dict_cls():
    cls = dict_cls(key_converter=str, key_validator=str, key_types=(str,), key_subtypes=True, **_RELATIONSHIP_KWARGS)
    assert issubclass(cls, DictStructure)
    assert cls.relationship == Relationship(extra_paths=(__name__,), **_KEY_RELATIONSHIP_KWARGS)
    assert cls.value_relationship == Relationship(extra_paths=(__name__,), **_RELATIONSHIP_KWARGS)


def test_list_cls():
    cls = list_cls(**_RELATIONSHIP_KWARGS)
    assert issubclass(cls, ListStructure)
    assert cls.relationship == Relationship(extra_paths=(__name__,), **_RELATIONSHIP_KWARGS)


def test_set_cls():
    cls = set_cls(**_RELATIONSHIP_KWARGS)
    assert issubclass(cls, SetStructure)
    assert cls.relationship == Relationship(extra_paths=(__name__,), **_RELATIONSHIP_KWARGS)


def test_attribute():
    attr = attribute(**_RELATIONSHIP_KWARGS)
    assert isinstance(attr, Attribute)
    assert attr.relationship == Relationship(extra_paths=(__name__,), **_RELATIONSHIP_KWARGS)


def test_dict_attribute():
    cls = dict_cls(qualified_name="DictClass")

    class MyClass(ImmutableClass):
        attr = dict_attribute(base_type=cls, **_RELATIONSHIP_KWARGS)

    assert isinstance(MyClass.attr, Attribute)
    assert issubclass(getattr(MyClass.attr.namespace, cls.__name__), cls)


def test_list_attribute():
    cls = list_cls(qualified_name="ListClass")

    class MyClass(ImmutableClass):
        attr = list_attribute(base_type=cls, **_RELATIONSHIP_KWARGS)

    assert isinstance(MyClass.attr, Attribute)
    assert issubclass(getattr(MyClass.attr.namespace, cls.__name__), cls)


def test_set_attribute():
    cls = set_cls(qualified_name="SetClass")

    class MyClass(ImmutableClass):
        attr = set_attribute(base_type=cls, **_RELATIONSHIP_KWARGS)

    assert isinstance(MyClass.attr, Attribute)
    assert issubclass(getattr(MyClass.attr.namespace, cls.__name__), cls)


if __name__ == "__main__":
    pytest.main()
