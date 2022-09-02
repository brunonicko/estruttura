import abc
import inspect

import six
import slotted
from basicco import explicit_hash, runtime_final, qualname
from tippo import Any, TypeVar, Iterator


T_co = TypeVar("T_co", covariant=True)


class BaseMeta(slotted.SlottedABCMeta, explicit_hash.ExplicitHashMeta, runtime_final.FinalizedMeta):
    """
    Metaclass for :class:`Base`.

    Features:
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Automatically decorates `__init__` methods to update the `initializing` tag.
      - Prevents base class attributes from being modified.
      - Runtime checking for `final` decorated classes/methods.
      - Implements `__fullname__` class property for back-porting qualified name.
    """

    @property
    def __fullname__(cls):
        # type: () -> str
        """Qualified name."""
        return qualname.qualname(cls, fallback=cls.__name__)


class Base(six.with_metaclass(BaseMeta, slotted.SlottedABC)):
    """
    Base class.

    Features:
      - Defines a `__weakref__` slot.
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Default implementation of `__copy__` raises an error.
      - Default implementation of `__ne__` returns the opposite of `__eq__`.
      - Prevents base class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Simplified `__dir__` result that shows only relevant members for client code.
      - Implements `__fullname__` class property for back-porting qualified name.
    """

    __slots__ = ("__weakref__",)

    def __copy__(self):
        """
        Prevents shallow copy by default.

        :raises RuntimeError: Always raised.
        """
        error = "{!r} objects can't be shallow copied".format(type(self).__fullname__)
        raise RuntimeError(error)

    def __repr__(self):
        # type: () -> str
        """
        Get representation using the class' full name if possible.

        :return: Representation.
        """
        return "<{} at {}>".format(type(self).__fullname__, hex(id(self)))

    def __ne__(self, other):
        # type: (object) -> bool
        """
        Compare for inequality by negating the result of `__eq__`.
        This is a backport of the default python 3 behavior to python 2.

        :param other: Another object.
        :return: True if not equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __dir__(self):
        # type: () -> list[str]
        """
        Get a simplified list of member names.

        :return: Simplified list of member names.
        """
        member_names = set()  # type: set[str]
        for base in reversed(inspect.getmro(type(self))):
            if base is object or base is type:
                continue
            member_names.update(n for n in base.__dict__ if not ("__" in n and n.startswith("_")))
        return sorted(member_names)


class BaseGenericMeta(BaseMeta, slotted.SlottedABCGenericMeta):  # type: ignore
    """
    Metaclass for generic :class:`BaseGeneric` classes.

    Features:
      - Allows for generic bases in Python 2.7.
    """


if slotted.SlottedABCGenericMeta is type:
    BaseGenericMeta = slotted.SlottedABCGenericMeta  # type: ignore  # noqa


class BaseGeneric(six.with_metaclass(BaseGenericMeta, Base)):
    """
    Generic base class.

    Features:
        - Allows for generic bases in Python 2.7.
    """


class BaseHashable(Base, slotted.SlottedHashable):
    """
    Base hashable.

    Features:
      - Forces implementation of `__hash__` method.
    """

    __slots__ = ()

    @abc.abstractmethod
    def __hash__(self):
        # type: () -> int
        raise NotImplementedError()


class BaseSized(Base, slotted.SlottedSized):
    """
    Base sized.

    Features:
      - Forces implementation of `__len__` method.
    """

    __slots__ = ()

    # noinspection PyProtocol
    @abc.abstractmethod
    def __len__(self):
        # type: () -> int
        raise NotImplementedError()


class BaseIterable(BaseGeneric, slotted.SlottedIterable[T_co]):
    """
    Base iterable.

    Features:
      - Forces implementation of `__iter__` method.
    """

    __slots__ = ()

    @abc.abstractmethod
    def __iter__(self):
        # type: () -> Iterator[T_co]
        raise NotImplementedError()


class BaseContainer(BaseGeneric, slotted.SlottedContainer[T_co]):
    """
    Base container.

    Features:
      - Forces implementation of `__contains__` method.
    """

    __slots__ = ()

    @abc.abstractmethod
    def __contains__(self, content):
        # type: (object) -> bool
        raise NotImplementedError()


# Trick static type checking.
SlottedCollection = slotted.SlottedCollection
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


class BaseCollection(BaseSized, BaseIterable[T_co], BaseContainer[T_co], SlottedCollection):
    """
    Base collection.

    Features:
      - Sized iterable container.
      - Forces implementation of `find` method.
    """

    __slots__ = ()

    @abc.abstractmethod
    def find(self, **query):
        # type: (**Any) -> list[T_co]
        """
        Find values that match a query.

        :param query: Query.
        :return: Matching values.
        """
        raise NotImplementedError()


class BaseProtectedCollection(BaseCollection[T_co]):
    """
    Base protected collection.

    Features:
      - Has protected transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
      - Forces implementation of `_clear` method.
    """

    __slots__ = ()

    @abc.abstractmethod
    def _clear(self):
        # type: (BPC) -> BPC
        """
        Clear.

        :return: Transformed.
        """
        raise NotImplementedError()


BPC = TypeVar("BPC", bound=BaseProtectedCollection)


# noinspection PyAbstractClass
class BaseInteractiveCollection(BaseProtectedCollection[T_co]):
    """
    Base interactive collection.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: (BIC) -> BIC
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


BIC = TypeVar("BIC", bound="BaseInteractiveCollection")


# noinspection PyAbstractClass
class BaseMutableCollection(BaseProtectedCollection[T_co]):
    """
    Base mutable collection.

    Features:
      - Has public mutable transformation and magic methods.
    """

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()
