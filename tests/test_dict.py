# type: ignore

import pytest
from slotted import SlottedMapping, SlottedMutableMapping
from tippo import ItemsView, KeysView, ValuesView

from estruttura import CollectionStructure, DictStructure, ImmutableCollectionStructure
from estruttura import ImmutableDictStructure, MutableCollectionStructure
from estruttura import MutableDictStructure
from estruttura.concrete import ImmutableDict, MutableDict


def test_inheritance():
    assert issubclass(DictStructure, CollectionStructure)
    assert issubclass(DictStructure, SlottedMapping)
    assert issubclass(ImmutableDictStructure, DictStructure)
    assert issubclass(ImmutableDictStructure, ImmutableCollectionStructure)
    assert issubclass(MutableDictStructure, DictStructure)
    assert issubclass(MutableDictStructure, MutableCollectionStructure)
    assert issubclass(MutableDictStructure, SlottedMutableMapping)

    assert issubclass(ImmutableDict, ImmutableDictStructure)
    assert issubclass(MutableDict, MutableDictStructure)


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_fromkeys(cls):
    dct = cls.fromkeys(("foo", "bar"), 1)
    assert dct == {"foo": 1, "bar": 1}
    assert dct["foo"] == 1
    assert dct["bar"] == 1


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_getitem(cls):
    dct = cls({"foo": 1, "bar": 2})
    assert dct["foo"] == 1
    assert dct["bar"] == 2
    with pytest.raises(KeyError):
        _ = dct["foobar"]


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_get(cls):
    dct = cls({"foo": 1})
    assert dct.get("foo") == 1
    assert dct.get("foobar", 2) == 2
    assert dct.get("foobar") is None


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_eq(cls):
    dct = cls({"foo": 1, "bar": 2})
    assert dct == dct
    assert dct == {"foo": 1, "bar": 2}
    assert dct != {"foo": 2, "bar": 1}


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_keys(cls):
    dct = cls({"foo": 1, "bar": 2})
    assert set(dct.keys()) == {"foo", "bar"}
    assert isinstance(dct.keys(), KeysView)


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_values(cls):
    dct = cls({"foo": 1, "bar": 2})
    assert set(dct.values()) == {1, 2}
    assert isinstance(dct.values(), ValuesView)


@pytest.mark.parametrize("cls", (MutableDict, ImmutableDict))
def test_items(cls):
    dct = cls({"foo": 1, "bar": 2})
    assert set(dct.items()) == {("foo", 1), ("bar", 2)}
    assert isinstance(dct.items(), ItemsView)


def test_setitem():
    dct = MutableDict({"foo": 2, "bar": 1})
    dct["foo"] = 1
    dct["bar"] = 2
    assert dct["foo"] == 1
    assert dct["bar"] == 2


def test_delitem():
    dct = MutableDict({"foo": 1, "bar": 2})
    del dct["foo"]
    assert dct["bar"] == 2
    with pytest.raises(KeyError):
        _ = dct["foo"]
    del dct["bar"]
    with pytest.raises(KeyError):
        _ = dct["bar"]


def test_immutable_discard():
    dct_a = ImmutableDict({"foo": 1, "bar": 2, "foobar": 3})
    dct_b = dct_a.discard("foo", "foobar", "zoo")
    assert dct_b == {"bar": 2}


def test_mutable_discard():
    dct = MutableDict({"foo": 1, "bar": 2, "foobar": 3})
    dct.discard("foo", "foobar", "zoo")
    assert dct == {"bar": 2}


def test_immutable_remove():
    dct_a = ImmutableDict({"foo": 1, "bar": 2, "foobar": 3})
    dct_b = dct_a.remove("foo", "foobar")
    assert dct_b == {"bar": 2}
    with pytest.raises(KeyError):
        dct_a.remove("zoo")


def test_mutable_remove():
    dct = MutableDict({"foo": 1, "bar": 2, "foobar": 3})
    dct.remove("foo", "foobar")
    assert dct == {"bar": 2}
    with pytest.raises(KeyError):
        dct.remove("zoo")


def test_immutable_set():
    dct_a = ImmutableDict({"foo": 1})
    dct_b = dct_a.set("foo", 2)
    assert dct_b["foo"] == 2
    dct_c = dct_b.set("foobar", 3)
    assert dct_c["foobar"] == 3


def test_mutable_set():
    dct = MutableDict({"foo": 1})
    dct.set("foo", 2)
    assert dct["foo"] == 2
    dct.set("foobar", 3)
    assert dct["foobar"] == 3


def test_mutable_clear():
    dct = MutableDict({"foo": 1, "bar": 2})
    dct.clear()
    assert not dct
    assert dct == MutableDict()
    assert dct == {}


def test_immutable_clear():
    dct_a = ImmutableDict({"foo": 1, "bar": 2})
    dct_b = dct_a.clear()
    assert dct_a
    assert not dct_b
    assert dct_b == ImmutableDict()
    assert dct_b == {}


def test_pop():
    dct = MutableDict({"foo": 1, "bar": 2})
    assert dct.pop("foo") == 1
    assert "foo" not in dct
    assert "bar" in dct


def test_popitem():
    dct = MutableDict({"foo": 1})
    assert dct.popitem() == ("foo", 1)
    assert not dct


def test_setdefault():
    dct = MutableDict({"foo": 1})
    assert dct.setdefault("foo", 2) == 1
    assert dct.setdefault("bar", 2) == 2
    assert "bar" in dct


def test_mutable_update():
    dct = MutableDict()
    dct.update({"foo": 1}, bar=2)
    assert dct == {"foo": 1, "bar": 2}


def test_immutable_update():
    dct_a = ImmutableDict()
    dct_b = dct_a.update({"foo": 1}, bar=2)
    assert dct_b == {"foo": 1, "bar": 2}


if __name__ == "__main__":
    pytest.main()
