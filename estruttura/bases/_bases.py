import abc

import six
import slotted
from basicco import explicit_hash, runtime_final, qualname, namespace, get_mro
from tippo import TypeVar, Iterator


T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseMeta(
    slotted.SlottedABCGenericMeta,
    explicit_hash.ExplicitHashMeta,
    runtime_final.FinalizedMeta,
    namespace.NamespacedMeta,
):
    """
    Metaclass for :class:`Base`.

    Features:
      - Implements abstract method checking and better support for generics in Python 2.7.
      - Protected class namespace available as `__namespace__`.
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Prevents class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Implements `__fullname__` class property for back-porting qualified name.
    """

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):
        dct = dict(dct)
        dct["__locked__"] = False
        return super(BaseMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)

    def __init__(cls, name, bases, dct, **kwargs):
        super(BaseMeta, cls).__init__(name, bases, dct, **kwargs)
        cls.__locked__ = True

    @property
    def __fullname__(cls):
        # type: () -> str
        """Qualified name."""
        return qualname.qualname(cls, fallback=cls.__name__)

    def __setattr__(cls, name, value):
        """Prevent setting class attributes."""
        if cls.__locked__:
            error = "{!r} class attributes are read-only".format(cls.__name__)
            raise AttributeError(error)
        super(BaseMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        """Prevent deleting class attributes."""
        if cls.__locked__:
            error = "{!r} class attributes are read-only".format(cls.__name__)
            raise AttributeError(error)
        super(BaseMeta, cls).__delattr__(name)


class Base(six.with_metaclass(BaseMeta, slotted.SlottedABC)):
    """
    Base class.

    Features:
      - Defines a `__weakref__` slot.
      - Implements abstract method checking and better support for generics in Python 2.7.
      - Protected class namespace available as `__namespace__`.
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Default implementation of `__ne__` returns the opposite of `__eq__`.
      - Prevents class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Simplified `__dir__` result that shows only relevant members for client code.
      - Implements `__fullname__` class property for back-porting qualified name.
    """

    __slots__ = ("__weakref__",)

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
        for base in reversed(get_mro.get_mro(type(self))):
            if base is object or base is type:
                continue
            member_names.update(n for n in base.__dict__ if not ("__" in n and n.startswith("_")))
        return sorted(member_names)


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


class BaseIterable(Base, slotted.SlottedIterable[T_co]):
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


class BaseContainer(Base, slotted.SlottedContainer[T_co]):
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


class BaseCollectionMeta(BaseMeta):
    """Metaclass for :class:`BaseCollection`."""


# Trick static type checking.
SlottedCollection = slotted.SlottedCollection
if SlottedCollection is None:
    globals()["SlottedCollection"] = object
assert SlottedCollection is not None


# noinspection PyAbstractClass
class BaseCollection(
    six.with_metaclass(BaseCollectionMeta, BaseSized, BaseIterable[T_co], BaseContainer[T_co], SlottedCollection)
):
    """
    Base collection.

    Features:
      - Sized iterable container.
      - Forces implementation of `find` method.
    """

    __slots__ = ()


class BasePrivateCollection(BaseCollection[T_co]):
    """
    Base private collection.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
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


BPC = TypeVar("BPC", bound=BasePrivateCollection)  # base private collection type


# noinspection PyAbstractClass
class BaseInteractiveCollection(BasePrivateCollection[T_co]):
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


BIC = TypeVar("BIC", bound="BaseInteractiveCollection")  # base interactive collection type


# noinspection PyAbstractClass
class BaseMutableCollection(BasePrivateCollection[T_co]):
    """
    Base mutable collection.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    @runtime_final.final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()
