import abc

import six
import slotted
from basicco import (
    explicit_hash,
    runtime_final,
    qualname,
    init_subclass,
    set_name,
    fabricate_value,
    recursive_repr,
    custom_repr,
    get_mro,
    type_checking,
)
from tippo import Any, Callable, Type, TypeVar, Iterator, Iterable, Generic, cast, overload

from ._constants import SupportsKeysAndGetItem


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type


class BaseMeta(
    slotted.SlottedABCGenericMeta,
    explicit_hash.ExplicitHashMeta,
    runtime_final.FinalizedMeta,
    set_name.SetNameMeta,
    init_subclass.InitSubclassMeta,
):
    """
    Metaclass for :class:`Base`.

    Features:
      - Implements abstract method checking and better support for generics in Python 2.7.
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Prevents class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Implements `__fullname__` class property for back-porting qualified name.
      - Support for back-ported `__set_name__` functionality.
      - Support for back-ported `__init_subclass__` functionality.
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


class Base(six.with_metaclass(BaseMeta, slotted.SlottedABC, set_name.SetName, init_subclass.InitSubclass)):
    """
    Base class.

    Features:
      - Defines a `__weakref__` slot.
      - Implements abstract method checking and better support for generics in Python 2.7.
      - Forces the use of `__slots__`.
      - Non-hashable by default.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Default implementation of `__ne__` returns the opposite of `__eq__`.
      - Prevents class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Simplified `__dir__` result that shows only relevant members for client code.
      - Implements `__fullname__` class property for back-porting qualified name.
      - Support for back-ported `__set_name__` functionality.
      - Support for back-ported `__init_subclass__` functionality.
    """

    __slots__ = ("__weakref__",)

    def __repr__(self):
        # type: () -> str
        """
        Get representation using the class' full name if possible.

        :return: Representation.
        """
        return "<{} at {}>".format(type(self).__fullname__, hex(id(self)))

    def __hash__(self):
        """Non-hashable by default."""
        error = "{!r} object is not hashable".format(type(self).__fullname__)
        raise TypeError(error)

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


# Set as non-hashable.
type.__setattr__(Base, "__hash__", None)


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


class Relationship(BaseHashable, Generic[T]):
    """Describes a relationship with values."""

    __slots__ = (
        "_converter",
        "_types",
        "_subtypes",
        "_serializer",
        "_deserializer",
        "_extra_paths",
        "_builtin_paths",
    )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        types=(),  # type: Iterable[Type[T] | Type | str | None] | Type[T] | Type | str | None
        subtypes=False,  # type: bool
        serializer=None,  # type: Callable[[T], Any] | str | None
        deserializer=None,  # type: Callable[[Any], T] | str | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param serializer: Callable value serializer.
        :param deserializer: Callable value deserializer.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        self._converter = fabricate_value.format_factory(converter)
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._serializer = fabricate_value.format_factory(serializer)
        self._deserializer = fabricate_value.format_factory(deserializer)
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

    @recursive_repr.recursive_repr
    def __repr__(self):
        items = self.to_items()
        return custom_repr.mapping_repr(
            mapping=dict(items),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            suffix=")",
            sorting=True,
            sort_key=lambda i, _s=self, _i=items: next(iter(zip(*_i))).index(i[0]),
            key_repr=str,
        )

    def __hash__(self):
        return hash(self.to_items())

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.to_items() == other.to_items()

    def convert(self, value):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self._converter,
            value,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def accepts_type(self, value):
        # type: (Any) -> bool
        return type_checking.is_instance(
            value,
            self._types,
            subtypes=self._subtypes,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def check_type(self, value):
        # type: (Any) -> T
        if self._types:
            return type_checking.assert_is_instance(
                value,
                self._types,
                subtypes=self._subtypes,
                extra_paths=self._extra_paths,
                builtin_paths=self._builtin_paths,
            )
        else:
            return value

    def process(self, value):
        # type: (Any) -> T
        return self.check_type(self.convert(value))

    def serialize(self, value, *args, **kwargs):
        # type: (T, *Any, **Any) -> Any
        return fabricate_value.fabricate_value(
            self._serializer,
            value,
            args=args,
            kwargs=kwargs,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def deserialize(self, serialized, *args, **kwargs):
        # type: (Any, *Any, **Any) -> T
        return fabricate_value.fabricate_value(
            self._deserializer,
            serialized,
            args=args,
            kwargs=kwargs,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("converter", self.converter),
            ("types", self.types),
            ("subtypes", self.subtypes),
            ("serializer", self.serializer),
            ("deserializer", self.deserializer),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    @runtime_final.final
    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    @overload
    def update(self, __m, **kwargs):
        # type: (R, SupportsKeysAndGetItem[str, Any], **Any) -> R
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (R, Iterable[tuple[str, Any]], **Any) -> R
        pass

    @overload
    def update(self, **kwargs):
        # type: (R, **Any) -> R
        pass

    def update(self, *args, **kwargs):
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(R, type(self)(**updated_kwargs))

    @property
    def converter(self):
        # type: () -> Callable[[Any], T] | Type[T] | str | None
        return self._converter

    @property
    def types(self):
        # type: () -> tuple[Type[T] | Type | str | None, ...]
        """Types for runtime checking."""
        return self._types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self._subtypes

    @property
    def serializer(self):
        # type: () -> Callable[[T], Any] | str | None
        """Callable value serializer."""
        return self._serializer

    @property
    def deserializer(self):
        # type: () -> Callable[[Any], T] | str | None
        """Callable value deserializer."""
        return self._deserializer

    @property
    def extra_paths(self):
        # type: () -> tuple[str, ...]
        """Extra module paths in fallback order."""
        return self._extra_paths

    @property
    def builtin_paths(self):
        # type: () -> tuple[str, ...] | None
        """Builtin module paths in fallback order."""
        return self._builtin_paths


R = TypeVar("R", bound=Relationship)  # relationship type


class BaseCollectionMeta(BaseMeta):
    """Metaclass for :class:`BaseCollection`."""

    __relationship_type__ = Relationship  # type: Type[Relationship]


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
      - Optional relationship.
    """

    __slots__ = ()
    __relationship__ = None  # type: Relationship | None

    def __init_subclass__(cls, relationship=None, **kwargs):
        # type: (Relationship | None, **Any) -> None
        if relationship is not None:
            type_checking.assert_is_instance(relationship, cls.__relationship_type__)
            cls.__relationship__ = relationship
        super(BaseCollection, cls).__init_subclass__(**kwargs)  # noqa


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


BIC = TypeVar("BIC", bound=BaseInteractiveCollection)  # base interactive collection type


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


class ProxyCollection(BaseCollection[T_co]):
    """
    Proxy collection.

    Features:
      - Wraps a private/interactive/mutable collection.
    """

    __slots__ = ("__wrapped",)

    def __init__(self, wrapped):
        # type: (BasePrivateCollection[T_co]) -> None
        """
        :param wrapped: Base private/interactive/mutable collection.
        """
        self.__wrapped = wrapped

    def __repr__(self):
        return "{}({})".format(type(self).__fullname__, self._wrapped)

    @runtime_final.final
    def __iter__(self):
        # type: () -> Iterator[T_co]
        for v in iter(self._wrapped):
            yield v

    @runtime_final.final
    def __contains__(self, content):
        # type: (object) -> bool
        return content in self._wrapped

    @runtime_final.final
    def __len__(self):
        # type: () -> int
        return len(self._wrapped)

    @property
    def _wrapped(self):
        # type: () -> BasePrivateCollection[T_co]
        """Wrapped base private/interactive/mutable collection."""
        return self.__wrapped


class PrivateProxyCollection(ProxyCollection[T_co], BasePrivateCollection[T_co]):
    """
    Private proxy collection.

    Features:
      - Has private transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @runtime_final.final
    def _transform_wrapped(self, new_wrapped):
        # type: (PPC, BasePrivateCollection[T_co]) -> PPC
        if new_wrapped is self._wrapped:
            return self
        else:
            return type(self)(new_wrapped)

    @runtime_final.final
    def _clear(self):
        # type: (PPC) -> PPC
        """
        Clear.

        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._clear())  # noqa


PPC = TypeVar("PPC", bound=PrivateProxyCollection)  # private proxy collection type


class InteractiveProxyCollection(PrivateProxyCollection[T_co], BaseInteractiveCollection[T_co]):
    """
    Proxy interactive collection.

    Features:
      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()


class MutableProxyCollection(PrivateProxyCollection[T_co], BaseMutableCollection[T_co]):
    """
    Proxy mutable collection.

    Features:
      - Has public mutable transformation methods.
    """

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (BaseMutableCollection[T_co]) -> None
        """
        :param wrapped: Base mutable collection.
        """
        super(MutableProxyCollection, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> BaseMutableCollection[T_co]
        """Wrapped base mutable collection."""
        return cast(BaseMutableCollection[T_co], super(MutableProxyCollection, self)._wrapped)
