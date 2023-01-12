import pytest

from estruttura._attribute import Attribute, MutableAttribute, getter
from estruttura.examples import ImmutableClass, MutableClass


def test_post_methods():
    inits = []
    deserializes = []

    class A(MutableClass):
        def __post_init__(self):
            inits.append(True)

        def __post_deserialize__(self):
            deserializes.append(True)

    A()
    assert inits

    A.deserialize({})
    assert deserializes


def test_immutable_post_methods():
    inits = []
    deserializes = []
    changes = []

    class A(ImmutableClass):
        def __post_init__(self):
            inits.append(True)

        def __post_deserialize__(self):
            deserializes.append(True)

        def __post_change__(self):
            changes.append(True)

    A()
    assert inits

    a = A.deserialize({})
    assert deserializes

    a = a.update()
    assert changes


def test_attributes():
    class A(MutableClass):
        a = MutableAttribute()

    assert dict(A.__attribute_map__) == dict(A.attributes) == {"a": A.a}  # noqa

    class B(A):
        b = MutableAttribute()

    assert dict(B.__attribute_map__) == dict(B.attributes) == {"a": A.a, "b": B.b}  # noqa

    class C(B):
        c = MutableAttribute()

    assert dict(C.__attribute_map__) == dict(C.attributes) == {"a": A.a, "b": B.b, "c": C.c}  # noqa

    class AA(MutableClass):
        aa = MutableAttribute()

    assert dict(AA.__attribute_map__) == dict(AA.attributes) == {"aa": AA.aa}  # noqa

    class BB(AA, C):
        bb = MutableAttribute()

    assert (
        dict(BB.__attribute_map__)
        == dict(BB.attributes)  # noqa
        == {"aa": AA.aa, "bb": BB.bb, "a": A.a, "b": B.b, "c": C.c}
    )

    assert ImmutableClass.__attribute_type__ is Attribute
    assert MutableClass.__attribute_type__ is MutableAttribute


def test_attributes_override():
    class A(MutableClass):
        a = MutableAttribute()

    assert dict(A.__attribute_map__) == dict(A.attributes) == {"a": A.a}  # noqa

    with pytest.raises(TypeError):

        class B(A):  # noqa
            a = None

    class MyAttribute(MutableAttribute):
        pass

    class C(MutableClass):
        __attribute_type__ = MyAttribute
        c = MyAttribute()

    assert dict(C.__attribute_map__) == dict(C.attributes) == {"c": C.c}  # noqa

    class D(C):
        d = MyAttribute()

    assert dict(D.__attribute_map__) == dict(D.attributes) == {"c": C.c, "d": D.d}  # noqa

    with pytest.raises(TypeError):

        class E(D):  # noqa
            e = MutableAttribute()

    class X(MutableClass):
        a = MutableAttribute()

    with pytest.raises(TypeError):

        class Y(X):  # noqa
            __attribute_type__ = MyAttribute


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
