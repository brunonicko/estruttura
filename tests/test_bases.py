import abc

import pytest
import tippo
import slotted
from basicco import explicit_hash, runtime_final, qualname, init_subclass, set_name

from estruttura import BaseMeta, Base


def test_base():

    # Metaclass.
    assert isinstance(Base, BaseMeta)

    # Abstract method checking.
    assert issubclass(BaseMeta, abc.ABCMeta)
    assert issubclass(Base, getattr(abc, "ABC", object))

    # Better support for generics in Python 2.7.
    assert issubclass(BaseMeta, tippo.GenericMeta)

    # Forces the use of `__slots__`.
    assert issubclass(BaseMeta, slotted.SlottedMeta)

    # Forces `__hash__` to be declared if `__eq__` was declared.
    assert issubclass(BaseMeta, explicit_hash.ExplicitHashMeta)

    # Prevents class attributes from changing.
    assert Base.__locked__
    with pytest.raises(AttributeError):
        Base.foo = "bar"
    with pytest.raises(AttributeError):
        del Base.__locked__  # noqa

    # Runtime checking for `final` decorated classes/methods.
    assert issubclass(BaseMeta, runtime_final.FinalizedMeta)

    # Implements `__qualname__` class property for back-porting qualified name.
    assert Base.__qualname__ == qualname.qualname(Base)

    # Support for back-ported `__set_name__` functionality.
    assert issubclass(BaseMeta, set_name.SetNameMeta)
    assert issubclass(Base, set_name.SetName)

    # Support for back-ported `__init_subclass__` functionality.
    assert issubclass(BaseMeta, init_subclass.InitSubclassMeta)
    assert issubclass(Base, init_subclass.InitSubclass)

    # Defines a `__weakref__` slot.
    assert "__weakref__" in Base.__slots__

    # Non-hashable by default.
    assert Base.__hash__ is None

    # Default implementation of `__ne__` returns the opposite of `__eq__`.
    base_a = Base()
    base_b = Base()
    assert (base_a == base_a) is not (base_a != base_a)
    assert (base_b == base_b) is not (base_b != base_b)
    assert (base_a == base_b) is not (base_a != base_b)

    # Simplified `__dir__` result that shows only relevant members for client code.
    assert dir(Base()) == []


if __name__ == "__main__":
    pytest.main()
