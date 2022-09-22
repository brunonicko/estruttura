import collections

import six
from basicco import custom_repr, runtime_final, recursive_repr, fabricate_value
from tippo import Any, Callable, TypeVar, Iterable, Generic, TypeAlias, Type, Tuple, Protocol, overload, cast

from ._constants import SupportsKeysAndGetItem, MissingType, MISSING, DELETED, DEFAULT
from ._dict import BaseDict
from ._bases import BaseHashable
from ._relationship import Relationship


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


# noinspection PyAbstractClass
class ClassProtocol(Protocol):

    def __getitem__(self, name):
        # type: (str) -> Any
        raise NotImplementedError()


# noinspection PyAbstractClass
class MutableClassProtocol(ClassProtocol):

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        raise NotImplementedError()

    def __delitem__(self, name):
        # type: (str) -> None
        raise NotImplementedError()


_attribute_counter = 0


class Attribute(BaseHashable, Generic[T_co]):
    """Attribute descriptor."""

    __slots__ = (
        "_owner",
        "_name",
        "_default",
        "_factory",
        "_init",
        "_required",
        "_settable",
        "_deletable",
        "_delegated",
        "_repr",
        "_eq",
        "_hash",
        "_relationship",
        "_metadata",
        "_extra_paths",
        "_builtin_paths",
        "_order",
    )

    def __init__(
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        init=True,  # type: bool
        required=True,  # type: bool
        settable=True,  # type: bool
        deletable=True,  # type: bool
        delegated=True,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
        relationship=None,  # type: Relationship | None
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        global _attribute_counter

        # Ensure single default source.
        if default is not MISSING and factory is not MISSING:
            error = "can't declare both 'default' and 'factory'"
            raise ValueError(error)

        # Ensure safe hash.
        if hash is None:
            hash = eq
        if hash and not eq:
            error = "can't contribute to the hash if it's not contributing to the eq"
            raise ValueError(error)

        # Set attributes.
        self._owner = None  # type: Type[ClassProtocol] | None
        self._name = None  # type: str | None
        self._default = default
        self._factory = factory
        self._init = bool(init)
        self._required = bool(required)
        self._settable = bool(settable)
        self._deletable = bool(deletable)
        self._delegated = bool(delegated)
        self._repr = bool(repr)
        self._eq = bool(eq)
        self._hash = bool(hash)
        self._relationship = relationship
        self._metadata = metadata
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        # Increment order counter.
        _attribute_counter += 1
        self._order = _attribute_counter

    def __hash__(self):
        return hash(self.to_items())

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.to_items() == other.to_items()

    @recursive_repr.recursive_repr
    def __repr__(self):
        items = self.to_items()
        return custom_repr.mapping_repr(
            mapping=dict(items),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            separator=", ",
            suffix=")",
            sorting=True,
            sort_key=lambda i, _s=self, _i=items: next(iter(zip(*_i))).index(i[0]),
            key_repr=str,
        )

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, None) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, Type[ClassProtocol]) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (ClassProtocol, Type[ClassProtocol]) -> T_co
        pass

    def __get__(self, instance, owner):
        if instance is not None:
            if self.name is None:
                assert self.owner is None
                error = "attribute not named/owned"
                raise RuntimeError(error)
            return instance[self.name]
        return self

    def __set_name__(self, owner, name):
        # type: (Type[ClassProtocol], str) -> None
        if self._name is not None and self._name != name:
            error = "attribute already named {!r}, can't rename it to {!r}".format(self._name, name)
            raise TypeError(error)
        if self._owner is not None and self._owner is not owner:
            error = "attribute already owned by {!r}, can't be owned by {!r} as well".format(
                self._owner.__name__, owner.__name__
            )
            raise TypeError(error)
        self._owner = owner
        self._name = name

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("name", self.name),
            ("default", self.default),
            ("factory", self.factory),
            ("init", self.init),
            ("required", self.required),
            ("settable", self.settable),
            ("deletable", self.deletable),
            ("delegated", self.delegated),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("relationship", self.relationship),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    @overload
    def update(self, __m, **kwargs):
        # type: (A, SupportsKeysAndGetItem[str, Any], **Any) -> A
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (A, Iterable[Item], **Any) -> A
        pass

    @overload
    def update(self, **kwargs):
        # type: (A, **Any) -> A
        pass

    def update(self, *args, **kwargs):
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(A, type(self)(**updated_kwargs))

    def get_default_value(self, process=True):
        # type: (bool) -> T_co

        # Get/fabricate default value.
        if self.default is not MISSING:
            default_value = self.default
        elif self.factory is not MISSING:
            default_value = fabricate_value.fabricate_value(
                self.factory,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            error = "no valid default/factory"
            raise RuntimeError(error)

        # Process value.
        if process:
            default_value = self.process(default_value)

        return default_value

    def process(self, value):
        # type: (Any) -> T
        if self.relationship is not None:
            return self.relationship.process(value)
        return value

    @property
    def name(self):
        # type: () -> str | None
        return self._name

    @property
    def owner(self):
        # type: () -> Type[ClassProtocol] | None
        return self._owner

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
        """Whether to include in the `__init__` method."""
        return self._init

    @property
    def required(self):
        # type: () -> bool
        return self._init

    @property
    def settable(self):
        # type: () -> bool
        return self._settable

    @property
    def deletable(self):
        # type: () -> bool
        return self._deletable

    @property
    def delegated(self):
        # type: () -> bool
        return self._delegated

    @property
    def repr(self):
        # type: () -> bool
        """Whether to include in the `__repr__` method."""
        return self._repr

    @property
    def eq(self):
        # type: () -> bool
        """Whether to include in the `__eq__` method."""
        return self._eq

    @property
    def hash(self):
        # type: () -> bool
        """Whether to include in the `__hash__` method."""
        return self._hash

    @property
    def relationship(self):
        # type: () -> Relationship | None
        return self._relationship

    @property
    def metadata(self):
        # type: () -> Any
        """User metadata."""
        return self._metadata

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
        return self._order

    @property
    def has_default(self):
        # type: () -> bool
        return self._default is not MISSING or self._factory is not MISSING


A = TypeVar("A", bound=Attribute)  # attribute type
AT_co = TypeVar("AT_co", bound=Attribute, covariant=True)  # covariant attribute type


class MutableAttribute(Attribute[T]):
    """Mutable attribute descriptor."""

    __slots__ = ()

    def __set__(self, instance, value):
        # type: (MutableClassProtocol, T) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        instance[self.name] = value

    def __delete__(self, instance):
        # type: (MutableClassProtocol) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        del instance[self.name]


@runtime_final.final
class AttributeMap(BaseDict[str, AT_co]):
    """Maps attributes by name."""

    __slots__ = ("__attribute_dict",)

    def __init__(self, attribute_items=()):
        # type: (Iterable[tuple[str, AT_co]]) -> None
        """
        :param attribute_items: Attribute items (name, attribute).
        """
        self.__attribute_dict = collections.OrderedDict()  # type: collections.OrderedDict[str, AT_co]
        for name, attribute in attribute_items:
            self.__attribute_dict[name] = attribute

    def __repr__(self):
        return "{}({})".format(type(self).__fullname__, custom_repr.iterable_repr(self.items()))

    def __hash__(self):
        return hash(tuple(self.__attribute_dict.items()))

    def __eq__(self, other):
        return isinstance(other, AttributeMap) and self.__attribute_dict == other.__attribute_dict

    def __getitem__(self, name):
        return self.__attribute_dict[name]

    def __contains__(self, name):
        return name in self.__attribute_dict

    def get(self, name, fallback=None):
        return self.__attribute_dict.get(name, fallback)

    def iteritems(self):
        for name, attribute in six.iteritems(self.__attribute_dict):
            yield (name, attribute)

    def iterkeys(self):
        for name in six.iterkeys(self.__attribute_dict):
            yield name

    def itervalues(self):
        for attribute in six.itervalues(self.__attribute_dict):
            yield attribute

    def __len__(self):
        return len(self.__attribute_dict)

    def __iter__(self):
        for name in six.iterkeys(self.__attribute_dict):
            yield name

    def get_initial_values(self, *args, **kwargs):
        # type: (*Any, **Any) -> dict[str, Any]
        """
        Get initial attribute values.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Initial attribute values.
        """

        # Go through each attribute.
        i = 0
        reached_kwargs = False
        internal_attribute_names = set()
        initial_values = {}
        for attribute_name, attribute in six.iteritems(self):

            # Skip non-init attributes.
            if not attribute.init:

                # Can't get its value from the init.
                if attribute_name in kwargs:
                    error = "attribute {!r} can't be set externally".format(attribute_name)
                    raise TypeError(error)

                if attribute.has_default:

                    # Has a default value.
                    value = attribute.get_default_value()
                    initial_values[attribute_name] = value
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
                    if value is DEFAULT:
                        if attribute.has_default:
                            value = attribute.get_default_value(process=False)
                        else:
                            error = "missing value for attribute {!r}".format(attribute_name)
                            raise ValueError(error)
                    i += 1
                    initial_values[attribute_name] = attribute.process(value)
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[attribute_name]
                if value is DEFAULT:
                    raise KeyError()
            except KeyError:
                if attribute.has_default:
                    value = attribute.get_default_value(process=False)
                elif attribute.required:
                    error = "missing value for required attribute {!r}".format(attribute_name)
                    exc = TypeError(error)
                    six.raise_from(exc, None)
                    raise exc
                else:
                    continue

            # Set attribute value.
            initial_values[attribute_name] = attribute.process(value)

        # Invalid kwargs.
        invalid_kwargs = set(kwargs).difference(self)
        if invalid_kwargs:
            error = "invalid keyword argument(s) {}".format(", ".join(repr(k) for k in invalid_kwargs))
            raise TypeError(error)

        # Invalid positional arguments.
        invalid_args = args[i:]
        if invalid_args:
            error = "invalid additional positional argument value(s) {}".format(
                ", ".join(repr(p) for p in invalid_args)
            )
            raise TypeError(error)

        return initial_values
