import pytest

from estruttura._attribute import Attribute, MutableAttribute, getter
from estruttura.examples import ImmutableClass, MutableClass


def test_init():
    class Point(MutableClass):
        x = MutableAttribute()
        y = MutableAttribute()

    assert Point(3, 4).serialize() == {"x": 3, "y": 4}
    assert Point(3, y=4).serialize() == {"x": 3, "y": 4}
    assert Point(x=3, y=4).serialize() == {"x": 3, "y": 4}

    with pytest.raises(TypeError):
        Point(3, 4, x=3, y=4)

    with pytest.raises(TypeError):
        Point(3, x=3, y=4)

    with pytest.raises(TypeError):
        Point(3, 4, y=4)

    with pytest.raises(TypeError):
        Point(3, 4, z=5)

    with pytest.raises(TypeError):
        Point(3, 4, 5)


def test_kw_only():
    class Point(MutableClass):
        __kw_only__ = True
        x = MutableAttribute()
        y = MutableAttribute()

    with pytest.raises(TypeError):
        Point(3, 4)

    with pytest.raises(TypeError):
        Point(3, y=4)

    assert Point(x=3, y=4).serialize() == {"x": 3, "y": 4}


def test_immutable():
    class Point(ImmutableClass):
        x = Attribute()
        y = Attribute()

    p = Point(3, 4)

    with pytest.raises(AttributeError):
        p.x = 30

    p = p.update(x=30)
    assert p.x == 30


class Foo(MutableClass):
    y = MutableAttribute(default=None, init=False, serializable=False)
    x = MutableAttribute()  # type: ignore
    _y = MutableAttribute(default=10, init_as=y, serialize_as=y)  # type: ignore


def test_init_as():
    foo = Foo(3, y=4)
    assert foo.x == 3
    assert foo._y == 4
    assert foo.y is None
    assert repr(foo) == "Foo(3, y=4)"
    assert foo.serialize() == {"x": 3, "y": 4}
    assert foo._internal == {"_y": 4, "x": 3, "y": None}
    assert Foo.deserialize({"x": 3, "y": 4}) == foo


class Bar(MutableClass):
    x = MutableAttribute()  # type: ignore
    _x = MutableAttribute(init_as=x, serialize_as=x)

    @getter(x, dependencies=(_x,))
    def _(self):
        return self._x * 2


def test_delegated_init_as():
    bar = Bar(1)
    assert bar.x == 2
    assert repr(bar) == "Bar(1)"
    assert bar.serialize() == {"x": 1}
    assert Bar.deserialize({"x": 1}) == bar

    with pytest.raises(AttributeError):
        bar.x = 10


if __name__ == "__main__":
    pytest.main()
