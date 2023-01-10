import pytest
from basicco import SlottedBase

from estruttura._attribute import (
    Attribute,
    AttributeMap,
    MutableAttribute,
    get_global_attribute_count,
)
from estruttura._relationship import Relationship


def test_init():
    start_count = get_global_attribute_count()

    with pytest.raises(ValueError):
        Attribute(default=3.14, factory=lambda: 3.14)

    with pytest.raises(ValueError):
        Attribute(serialize_default=False)

    with pytest.raises(ValueError):
        Attribute(hash=True, eq=False)

    with pytest.raises(ValueError):
        Attribute(order=True, eq=False)

    with pytest.raises(ValueError):
        Attribute(order=True, required=False)

    Attribute()
    assert get_global_attribute_count() == start_count + 1


def test_default():
    attribute = Attribute(default=3.14)
    assert attribute.default == 3.14

    relationship = Relationship(types=(float,), converter=float)
    attribute = Attribute(default="3.14", relationship=relationship)  # type: ignore
    assert attribute.default == "3.14"
    assert attribute.get_default_value() == "3.14"
    assert attribute.process_value(attribute.get_default_value()) == 3.14

    attribute = Attribute(factory=lambda: "3.14", relationship=relationship)  # type: ignore
    assert attribute.get_default_value() == "3.14"
    assert attribute.process_value(attribute.get_default_value()) == 3.14


def test_constant():
    with pytest.raises(ValueError):
        Attribute(constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, factory=float, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, required=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, init=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, settable=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, deletable=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, serializable=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, repr=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, eq=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, order=True, constant=True)

    with pytest.raises(ValueError):
        Attribute(3.14, hash=True, constant=True)

    attribute = Attribute(3.14, constant=True)

    class MyClass(SlottedBase):
        PI = attribute

    assert MyClass.PI == 3.14
    assert MyClass.PI == attribute.constant_value

    attribute = Attribute(
        "3.14", constant=True, relationship=Relationship(types=(float,), converter=float)  # type: ignore
    )

    class MyClass(SlottedBase):
        PI = attribute

    assert MyClass.PI == 3.14
    assert MyClass.PI == attribute.constant_value


class _MutableAttributed(SlottedBase):
    __slots__ = ()

    @classmethod
    def _attr(cls, name):
        name = "_{}".format(name)
        if name not in cls.__slots__:
            raise AttributeError(name)
        return name

    def __init__(self, **values):
        for name, value in values.items():
            setattr(self, self._attr(name), value)

    def __getitem__(self, name):
        return getattr(self, self._attr(name))

    def __setitem__(self, name, value):
        setattr(self, self._attr(name), value)

    def __delitem__(self, name):
        delattr(self, self._attr(name))

    def __iter__(self):
        for name in type(self).__slots__:
            if name in self:
                yield name, self[name]

    def __contains__(self, name):
        return hasattr(self, name) and "_{}".format(name) in type(self).__slots__


def test_mutable():
    class MyClass(_MutableAttributed):
        __slots__ = ("_foo", "_bar")

        foo = MutableAttribute()
        bar = MutableAttribute()

    my_obj = MyClass(foo="foo", bar="bar")
    assert my_obj.foo == "foo"
    assert my_obj.bar == "bar"

    my_obj.foo = "FOO"
    assert my_obj.foo == "FOO"

    my_obj.bar = "BAR"
    assert my_obj.bar == "BAR"

    del my_obj.foo
    assert not hasattr(my_obj, "foo")

    del my_obj.bar
    assert not hasattr(my_obj, "bar")


def test_attribute_map():
    class MyClass(_MutableAttributed):
        __slots__ = ("_foo", "_bar")

        foo = MutableAttribute()
        bar = MutableAttribute()

    amap = AttributeMap([("foo", MyClass.foo), ("bar", MyClass.bar)])
    assert amap.get_initial_values(args=(3, 4), kwargs={}) == {"foo": 3, "bar": 4}
    assert amap.get_initial_values(args=(3,), kwargs={"bar": 4}) == {"foo": 3, "bar": 4}
    assert amap.get_initial_values(args=(), kwargs={"foo": 3, "bar": 4}) == {"foo": 3, "bar": 4}

    with pytest.raises(TypeError):
        amap.get_initial_values(args=(), kwargs={"foo": 3, "y": 4})

    with pytest.raises(TypeError):
        amap.get_initial_values(args=(3, 4), kwargs={"foo": 3, "bar": 4})

    with pytest.raises(TypeError):
        amap.get_initial_values(args=(3,), kwargs={"foo": 3, "bar": 4})

    with pytest.raises(TypeError):
        amap.get_initial_values(args=(3, 4, 5), kwargs={})


if __name__ == "__main__":
    pytest.main()
