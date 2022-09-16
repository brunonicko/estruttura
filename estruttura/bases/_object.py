import abc
import collections

import six
import enum
from basicco import runtime_final, mapping_proxy, fabricate_value
from tippo import Any, Callable, TypeVar, Tuple, Protocol, Iterable, Generic, Type, TypeAlias, overload

from ._bases import (
    Base,
    BaseCollectionMeta,
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BaseProtectedCollection,
)


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


class MissingType(enum.Enum):
    MISSING = "MISSING"


MISSING = MissingType.MISSING


class _SupportsKeysAndGetItem(Protocol):
    def keys(self):
        # type: () -> Iterable[str]
        pass

    def __getitem__(self, __k):
        # type: (str) -> Any
        pass


class BaseAttribute(Base, Generic[T_co]):
    __slots__ = ("_name", "_default", "_factory", "_init", "_required", "_extra_paths", "_builtin_paths", "__order")
    __counter = 0

    def __init__(
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        init=True,  # type: bool
        required=True,  # type: bool
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        if default is not MISSING and factory is not MISSING:
            error = "can't declare both 'default' and 'factory'"
            raise ValueError(error)

        self._name = None  # type: str | None
        self._default = default
        self._factory = factory
        self._init = bool(init)
        self._required = bool(required)
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        BaseAttribute.__counter += 1
        self.__order = BaseAttribute.__counter

    @abc.abstractmethod
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> T_co
        raise NotImplementedError()

    def make_default(self):
        # type: () -> T_co
        if self.default is not MISSING:
            return self.default
        elif self.factory is not MISSING:
            return fabricate_value.fabricate_value(
                self.factory,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            error = "no valid default/factory"
            raise RuntimeError(error)

    @property
    def name(self):
        # type: () -> str
        if self._name is None:
            error = "attribute name was never set"
            raise RuntimeError(error)
        return self._name

    @name.setter
    def name(self, value):
        # type: (str) -> None
        if self._name is not None and self._name != value:
            error = "attribute already named {!r}, can't rename it to {!r}".format(self._name, value)
            raise AttributeError(error)
        self._name = value

    @property
    def default(self):
        # type: () -> Any
        return self._default

    @property
    def factory(self):
        # type: () -> Callable[..., T_co] | str | MissingType
        return self._factory

    @property
    def init(self):
        # type: () -> bool
        return self._init

    @property
    def required(self):
        # type: () -> bool
        return self._init

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

    @property
    @runtime_final.final
    def order(self):
        # type: () -> int
        return self.__order

    @property
    def has_default(self):
        # type: () -> bool
        return self._default is not MISSING or self._factory is not MISSING


class AttributeInitializer(Base):
    __slots__ = ("_attributes",)

    def __init__(self, attributes):
        # type: (Iterable[tuple[str, BaseAttribute]]) -> None
        self._attributes = tuple(attributes)

    def get_values(self, *args, **kwargs):

        # Go through each attribute.
        i = 0
        reached_kwargs = False
        internal_attribute_names = set()
        init_values = {}
        for attribute_name, attribute in self.attributes:

            # Skip non-init attributes.
            if not attribute.init:

                # Can't get its value from the init.
                if attribute_name in kwargs:
                    error = "attribute {!r} can't be set externally".format(attribute_name)
                    raise TypeError(error)

                if attribute.has_default:

                    # Has a default value.
                    value = attribute.make_default()
                    init_values[attribute_name] = value
                    continue

                elif attribute.required:

                    # Keep track of non-init, required attribute names (internal attributes).
                    internal_attribute_names.add(attribute_name)

                continue

            # Get value for positional argument.
            if not reached_kwargs:
                try:
                    value = args[i]
                except IndexError:
                    reached_kwargs = True
                else:
                    i += 1
                    init_values[attribute_name] = value
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[attribute_name]
            except KeyError:
                if attribute.has_default:
                    value = attribute.make_default()
                elif attribute.required:
                    error = "missing value for required attribute {!r}".format(attribute_name)
                    exc = TypeError(error)
                    six.raise_from(exc, None)
                    raise exc
                else:
                    continue

            # Set attribute value.
            init_values[attribute_name] = value

        # Invalid kwargs.
        invalid_kwargs = set(kwargs).difference(dict(self.attributes))
        if invalid_kwargs:
            error = "invalid keyword argument(s) {}".format(", ".join(repr(k) for k in invalid_kwargs))
            raise TypeError(error)

        # Invalid positional arguments.
        invalid_args = args[i:]
        if invalid_args:
            error = "invalid additional positional argument(s) {}".format(", ".join(repr(p) for p in invalid_args))
            raise TypeError(error)

    @property
    def attributes(self):
        # type: () -> tuple[tuple[str, BaseAttribute], ...]
        return self._attributes


class BaseObjectMeta(BaseCollectionMeta, type):

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):
        # type: (...) -> BaseObjectMeta
        cls = super(BaseObjectMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)

        # Scrape attributes.
        attributes = _AttributeScraper(cls).scrape()
        type.__setattr__(cls, "__attributes__", attributes)

        # Name attributes.
        for attribute_name, attribute in six.iteritems(attributes):
            attribute.name = attribute_name

        # Check for non-default attributes declared after default ones.
        seen_default = None
        for attribute_name, attribute in six.iteritems(attributes):
            if not attribute.init:
                continue
            if attribute.has_default:
                seen_default = attribute_name
            elif seen_default is not None:
                error = "non-default attribute {!r} declared after default attribute {!r}".format(
                    attribute_name, seen_default
                )
                raise TypeError(error)

        return cls

    @property
    def __attributes__(cls):
        # type: () -> collections.OrderedDict[str, BaseAttribute]
        return cls.__namespace__.__attributes__


class BaseObject(six.with_metaclass(BaseObjectMeta, BaseCollection[Item])):
    """Base object."""

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: {!r}".format(type(self).__name__)
        raise TypeError(error)

    @abc.abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __getitem__(self, attribute_name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param attribute_name: Attribute name.
        :return: Value/values.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseObject, "__hash__", None)  # force non-hashable


BO = TypeVar("BO", bound=BaseObject)  # base object type


class BaseProtectedObject(BaseObject, BaseProtectedCollection[Item]):
    """Base protected object."""

    __slots__ = ()

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPM, _SupportsKeysAndGetItem, **Any) -> BPM
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BPM, Iterable[Item], **Any) -> BPM
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BPM, **Any) -> BPM
        pass

    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()


BPM = TypeVar("BPM", bound=BaseProtectedObject)  # base protected object type


# noinspection PyAbstractClass
class BaseInteractiveObject(BaseProtectedObject, BaseInteractiveCollection[Item]):
    """Base interactive object."""

    __slots__ = ()

    @overload
    def update(self, __m, **kwargs):
        # type: (BPM, _SupportsKeysAndGetItem, **Any) -> BPM
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BPM, Iterable[Item], **Any) -> BPM
        pass

    @overload
    def update(self, **kwargs):
        # type: (BPM, **Any) -> BPM
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


# noinspection PyAbstractClass
class BaseMutableObject(BaseProtectedObject, BaseMutableCollection[Item]):
    """Base mutable object."""

    __slots__ = ()

    @runtime_final.final
    def __setitem__(self, attribute_name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param attribute_name: Attribute name.
        :param value: Value.
        """
        self.update({attribute_name: value})

    @overload
    def update(self, __m, **kwargs):
        # type: (_SupportsKeysAndGetItem, **Any) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[Item], **Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        pass

    @runtime_final.final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)
