import pytest

from estruttura._attribute import MutableAttribute, getter
from estruttura.examples import MutableClass


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
        return self._x


def test_delegated_init_as():
    bar = Bar(1)
    assert bar.x == 1
    assert repr(bar) == "Bar(1)"
    assert bar.serialize() == {"x": 1}
    assert Bar.deserialize({"x": 1}) == bar

    with pytest.raises(AttributeError):
        bar.x = 10


if __name__ == "__main__":
    pytest.main()
