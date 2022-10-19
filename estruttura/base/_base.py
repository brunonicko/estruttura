import six
import basicco
import slotted
from basicco.abstract_class import abstract, is_abstract
from basicco.explicit_hash import set_to_none
from basicco.runtime_final import final
from tippo import TypeVar


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseMeta(basicco.SlottedBaseMeta):
    """Metaclass for :class:`Base`."""


class Base(six.with_metaclass(BaseMeta, basicco.SlottedBase)):
    """Forces the implementation of `__hash__` and `__eq__`."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()

    @abstract
    def __eq__(self, other):
        # type: (object) -> bool
        raise NotImplementedError()


class BaseImmutableMeta(BaseMeta):
    """Metaclass for :class:`BaseImmutable`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        cls = super(BaseImmutableMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)
        if cls.__hash__ is None:
            error = "{!r} in {!r} can't be None".format(cls.__hash__, name)
            raise TypeError(error)
        return cls


class BaseImmutable(six.with_metaclass(BaseImmutableMeta, Base, slotted.SlottedHashable)):
    """Forces an implementation of `__hash__` that is not None."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()


class BaseMutableMeta(BaseMeta):
    """Metaclass for :class:`BaseMutable`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):  # noqa
        if "__eq__" in dct and "__hash__" not in dct:
            dct = dict(dct)
            dct["__hash__"] = None
        cls = super(BaseMutableMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)
        if cls.__hash__ is not None and not is_abstract(cls.__hash__):
            error = "'__hash__' in {!r} needs to be None".format(name)
            raise TypeError(error)
        return cls


# noinspection PyAbstractClass
class BaseMutable(six.with_metaclass(BaseMutableMeta, Base)):
    """Non-hashable."""

    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)


# noinspection PyAbstractClass
class BaseCollection(Base, slotted.SlottedCollection[T_co]):
    """Base collection."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseImmutableCollection(BaseCollection[T_co], BaseImmutable):
    """Base immutable collection."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableCollection(BaseCollection[T_co], BaseMutable):
    """Base mutable collection."""

    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)


class BaseUniformCollection(BaseCollection[T_co]):

    __slots__ = ()

    @abstract
    def _clear(self):
        # type: (BUC) -> BUC
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        raise NotImplementedError()


BUC = TypeVar("BUC", bound=BaseUniformCollection)


# noinspection PyAbstractClass
class BaseImmutableUniformCollection(BaseUniformCollection[T_co], BaseImmutableCollection[T_co], BaseImmutable):
    """Has public immutable transformation methods that return a new version."""

    __slots__ = ()

    @final
    def clear(self):
        # type: (BIUC) -> BIUC
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BIUC = TypeVar("BIUC", bound=BaseImmutableUniformCollection)


# noinspection PyAbstractClass
class BaseMutableUniformCollection(BaseUniformCollection[T_co], BaseMutableCollection[T_co], BaseMutable):
    """Has public mutable transformation methods."""

    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()
