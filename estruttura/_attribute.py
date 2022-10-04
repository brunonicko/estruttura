import collections
import contextlib
import weakref

import six
import slotted
from basicco import (
    Base,
    BaseMeta,
    basic_data,
    custom_repr,
    fabricate_value,
    recursive_repr,
    runtime_final,
    safe_repr,
    unique_iterator,
)
from tippo import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Literal,
    Mapping,
    Protocol,
    SupportsKeysAndGetItem,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from ._constants import DEFAULT, DELETED, MISSING, MissingType
from ._relationship import Relationship

T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


_attribute_counter = 0


class Attribute(basic_data.ImmutableBasicData, Generic[T_co]):
    """Attribute descriptor."""

    __slots__ = (
        "_owner",
        "_name",
        "_default",
        "_factory",
        "_required",
        "_init",
        "_updatable",
        "_deletable",
        "_repr",
        "_eq",
        "_hash",
        "_relationship",
        "_dependencies",
        "_recursive_dependencies",
        "_dependents",
        "_recursive_dependents",
        "_fget",
        "_fset",
        "_fdel",
        "_metadata",
        "_extra_paths",
        "_builtin_paths",
        "_constant",
        "_order",
    )

    def __init__(
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        required=True,  # type: bool
        init=None,  # type: bool | None
        updatable=None,  # type: bool | None
        deletable=None,  # type: bool | None
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
        self._required = bool(required)
        self._init = bool(init) if init is not None else None
        self._updatable = bool(updatable) if updatable is not None else None
        self._deletable = bool(deletable) if deletable is not None else None
        self._repr = bool(repr)
        self._eq = bool(eq)
        self._hash = bool(hash)
        self._relationship = relationship
        self._dependencies = ()  # type: tuple[Attribute, ...]
        self._recursive_dependencies = None  # type: tuple[Attribute, ...] | None
        self._dependents = ()  # type: tuple[Attribute, ...]
        self._recursive_dependents = None  # type: tuple[Attribute, ...] | None
        self._fget = None  # type: Callable[[ClassProtocol], T_co] | None
        self._fset = None  # type: Callable[[ClassProtocol, T_co], None] | None
        self._fdel = None  # type: Callable[[ClassProtocol], None] | None
        self._metadata = metadata
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None
        self._constant = False

        # Increment order counter.
        _attribute_counter += 1
        self._order = _attribute_counter

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, None) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, Type[ClassProtocol]) -> A | T_co
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (ClassProtocol, Type[ClassProtocol]) -> T_co
        pass

    def __get__(self, instance, owner):
        if self.constant:
            return self.default
        if instance is not None:
            if self.name is None:
                assert self.owner is None
                error = "attribute not named/owned"
                raise RuntimeError(error)
            return instance[self.name]
        return self

    def __set_name__(self, owner, name):
        # type: (Type[ClassProtocol], str) -> None

        # Checks.
        if self._name is not None and self._name != name:
            error = "attribute already named {!r}, can't rename it to {!r}".format(self._name, name)
            raise TypeError(error)
        if self._owner is not None and self._owner is not owner:
            error = "attribute already owned by {!r}, can't be owned by {!r} as well".format(
                self._owner.__name__, owner.__name__
            )
            raise TypeError(error)

        # Resolve automatic parameters.
        if self.delegated:
            if self.init is None:
                self._init = False
            if self.updatable is None:
                self._updatable = self.fset is not None
            if self.deletable is None:
                self._deletable = self.fdel is not None
        else:
            if self.init is None:
                self._init = True
            if self.updatable is None:
                self._updatable = True
            if self.deletable is None:
                self._deletable = False
        assert not any(p is None for p in (self._init, self._updatable, self._deletable))

        # More checks.
        if self.delegated:
            if self.fset is None and self.init:
                error = "delegated attribute {!r} is in __init__ but has no setter delegate was defined".format(name)
                raise TypeError(error)
            if self.fset is None:
                if self.updatable:
                    error = "delegated attribute {!r} is updatable but has no setter delegate was defined".format(name)
                    raise TypeError(error)
                if self.has_default:
                    error = "delegated attribute {!r} has no setter but has a default".format(name)
                    raise TypeError(error)
            if self.fdel is None and self.deletable:
                error = "delegated attribute {!r} is deletable but has no deleter delegate was defined".format(name)
                raise TypeError(error)

        # Set owner and name.
        self._owner = owner
        self._name = name

        # If attribute is a constant, set flag and process value.
        if all(
            (
                self.default is not MISSING,
                not self.init,
                not self.repr,
                not self.eq,
                not self.hash,
                not self.updatable,
                not self.deletable,
                not self.delegated,
            )
        ):
            self.process(self.default)
            self._constant = True

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
        items = [
            ("default", self.default),
            ("factory", self.factory),
            ("required", self.required),
            ("init", self.init),
            ("updatable", self.updatable),
            ("deletable", self.deletable),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("relationship", self.relationship),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        ]
        if usecase is not basic_data.ItemUsecase.INIT:
            items.extend(
                [
                    ("name", self.name),
                    ("owner", self.owner),
                    ("delegated", self.delegated),
                    ("constant", self.constant),
                    ("order", self.order),
                ]
            )
            if usecase is not basic_data.ItemUsecase.REPR:
                items.extend(
                    [
                        ("dependencies", self.dependencies),
                        ("dependents", self.dependents),
                        ("fget", self.fget),
                        ("fset", self.fset),
                        ("fdel", self.fdel),
                    ]
                )
            elif self.owned and all(d.owned for d in self.dependencies):
                items.extend(
                    [
                        ("dependencies", [d.name for d in self.dependencies]),
                    ]
                )
        return items

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
        init_args = self.to_dict(basic_data.ItemUsecase.INIT)
        init_args.update(*args, **kwargs)
        return cast(A, type(self)(**init_args))

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
        # type: (Any) -> T_co
        if self.relationship is not None:
            try:
                return self.relationship.process(value)
            except Exception as e:
                exc = type(e)("{!r} attribute; {}".format(self.name, e))
                six.raise_from(exc, None)
                raise exc
        return value

    @overload
    def getter(self, maybe_func):
        # type: (A, Callable[[ClassProtocol], T_co]) -> A
        pass

    @overload
    def getter(self, *dependencies):
        # type: (A, *Attribute) -> A
        pass

    def getter(self, *dependencies):
        """
        Define a getter delegate method by using a decorator.

        :param dependencies: Attribute dependencies.
        :return: Getter method decorator.
        :raises ValueError: Cannot define a getter for a non-delegated attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Getter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """

        def getter_decorator(func):
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.fget is not None:
                error = "getter delegate already defined"
                raise ValueError(error)
            assert not self._dependencies

            self._dependencies = ()
            for dependency in unique_iterator.unique_iterator(dependencies):
                if dependency.owned:
                    error = "dependency attribute {!r} already named and owned by a class".format(dependency.name)
                    raise ValueError(error)
                dependency._dependents += (self,)  # noqa
                self._dependencies += (dependency,)

            self._fget = func
            return self

        if len(dependencies) == 1 and not isinstance(dependencies[0], Attribute) and callable(dependencies[0]):
            return getter_decorator(dependencies[0])
        else:
            return getter_decorator

    @overload
    def setter(self, maybe_func=None):
        # type: (A, None) -> Callable[[Callable[[ClassProtocol, T_co], None]], A]
        pass

    @overload
    def setter(self, maybe_func):
        # type: (A, Callable[[ClassProtocol, T_co], None]) -> A
        pass

    def setter(self, maybe_func=None):
        """
        Define a setter delegate method by using a decorator.

        :return: Setter method decorator.
        :raises ValueError: Cannot define a setter for a non-delegated attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not updatable.
        :raises ValueError: Need to define a getter before defining a setter.
        :raises ValueError: Setter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """

        def setter_decorator(func):
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.updatable is False:
                error = "attribute is not updatable, can't define setter delegate"
                raise ValueError(error)
            if self.fget is None:
                error = "need to define a getter delegate before defining a setter delegate"
                raise ValueError(error)
            if self.fset is not None:
                error = "setter delegate already defined"
                raise ValueError(error)
            self._fset = func
            return self

        if maybe_func is not None:
            return setter_decorator(maybe_func)
        else:
            return setter_decorator

    @overload
    def deleter(self, maybe_func=None):
        # type: (A, None) -> Callable[[Callable[[ClassProtocol], None]], A]
        pass

    @overload
    def deleter(self, maybe_func):
        # type: (A, Callable[[ClassProtocol], None]) -> A
        pass

    def deleter(self, maybe_func=None):
        """
        Define a deleter delegate method by using a decorator.

        :return: Deleter method decorator.
        :raises ValueError: Cannot define a deleter for a non-delegated attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not deletable.
        :raises ValueError: Need to define a getter before defining a deleter.
        :raises ValueError: Deleter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """

        def deleter_decorator(func):
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.deletable is False:
                error = "attribute is not deletable, can't define deleter delegate"
                raise ValueError(error)
            if self.fget is None:
                error = "need to define a getter delegate before defining a deleter delegate"
                raise ValueError(error)
            if self.fdel is not None:
                error = "deleter delegate already defined"
                raise ValueError(error)
            self._fdel = func
            return self

        if maybe_func is not None:
            return deleter_decorator(maybe_func)
        else:
            return deleter_decorator

    @property
    def name(self):
        # type: () -> str | None
        return self._name

    @property
    def owner(self):
        # type: () -> Type[ClassProtocol] | None
        return self._owner

    @property
    def owned(self):
        # type: () -> bool
        owned = self._owner is not None
        assert self._name is not None if owned else self._name is None
        return owned

    @property
    def default(self):
        # type: () -> Any
        return self._default

    @property
    def factory(self):
        # type: () -> Callable[..., T_co] | str | MissingType
        return self._factory

    @property
    def required(self):
        # type: () -> bool
        return self._required

    @property
    def init(self):
        # type: () -> bool | None
        """Whether to include in the `__init__` method."""
        return self._init

    @property
    def updatable(self):
        # type: () -> bool | None
        return self._updatable

    @property
    def deletable(self):
        # type: () -> bool | None
        return self._deletable

    @property
    def delegated(self):
        # type: () -> bool
        return any(d is not None for d in (self.fget, self.fset, self.fdel))

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
    def dependencies(self):
        # type: () -> tuple[Attribute, ...]
        return self._dependencies

    @property
    def recursive_dependencies(self):
        # type: () -> tuple[Attribute, ...]
        if self._recursive_dependencies is not None:
            return self._recursive_dependencies
        recursive_dependencies = _traverse(self, direction="dependencies")

        # Cache only if already owned.
        if self.owned:
            self._recursive_dependencies = recursive_dependencies

        return recursive_dependencies

    @property
    def dependents(self):
        # type: () -> tuple[Attribute, ...]
        return self._dependents

    @property
    def recursive_dependents(self):
        # type: () -> tuple[Attribute, ...]
        if self._recursive_dependents is not None:
            return self._recursive_dependents
        recursive_dependents = _traverse(self, direction="dependents")

        # Cache only if already owned.
        if self.owned:
            self._recursive_dependents = recursive_dependents

        return recursive_dependents

    @property
    def fget(self):
        # type: () -> Callable[[ClassProtocol], T_co] | None
        return self._fget

    @property
    def fset(self):
        # type: () -> Callable[[ClassProtocol, T_co], None] | None
        return self._fset

    @property
    def fdel(self):
        # type: () -> Callable[[ClassProtocol], None] | None
        return self._fdel

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
        return self.default is not MISSING or self.factory is not MISSING

    @property
    def constant(self):
        # type: () -> bool
        return self._constant


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
        if self.constant:
            error = "can't change constant class attribute {!r}".format(self.name)
            raise AttributeError(error)
        instance[self.name] = value

    def __delete__(self, instance):
        # type: (MutableClassProtocol) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        if self.constant:
            error = "can't delete constant class attribute {!r}".format(self.name)
            raise AttributeError(error)
        del instance[self.name]


class AttributeMapMeta(BaseMeta, slotted.SlottedABCGenericMeta):
    """Metaclass for :class:`AttributeMap`."""


@runtime_final.final
class AttributeMap(six.with_metaclass(AttributeMapMeta, Base, slotted.SlottedMapping[str, AT_co])):
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

    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        return "{}({})".format(type(self).__name__, custom_repr.iterable_repr(self.items()))

    def __hash__(self):
        # type: () -> int
        return hash(tuple(self.__attribute_dict.items()))

    def __eq__(self, other):
        # type: (object) -> bool
        return type(other) is type(self) and self.__attribute_dict == other.__attribute_dict  # type: ignore  # noqa

    def __getitem__(self, name):
        # type: (str) -> AT_co
        return self.__attribute_dict[name]

    def __contains__(self, name):
        # type: (object) -> bool
        return name in self.__attribute_dict

    def __len__(self):
        # type: () -> int
        return len(self.__attribute_dict)

    def __iter__(self):
        # type: () -> Iterator[str]
        for name in self.__attribute_dict:
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
        required_names = set()
        initial_values = {}  # type: dict[str, Any]
        for name, attribute in six.iteritems(self):

            # Keep track of required attribute names.
            if attribute.required:
                required_names.add(name)

            # Skip non-init attributes.
            if not attribute.init:

                # Can't get its value from the init.
                if name in kwargs:
                    error = "attribute {!r} can't be set externally".format(name)
                    raise TypeError(error)

                if attribute.has_default:

                    # Has a default value.
                    value = attribute.get_default_value(process=False)
                    initial_values[name] = value

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
                            error = "missing value for attribute {!r}".format(name)
                            raise ValueError(error)
                    i += 1
                    initial_values[name] = value
                    continue

            # Get value for keyword argument.
            try:
                value = kwargs[name]
                if value is DEFAULT:
                    raise KeyError()
            except KeyError:
                if attribute.has_default:
                    value = attribute.get_default_value(process=False)
                elif attribute.required:
                    error = "missing value for required attribute {!r}".format(name)
                    exc = TypeError(error)
                    six.raise_from(exc, None)
                    raise exc
                else:
                    continue

            # Set attribute value.
            initial_values[name] = value

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

        # Compile updates.
        initial_values, _ = self.get_update_values(initial_values)

        # Check for required attributes.
        missing = required_names.difference(initial_values)
        if missing:
            error = "missing values for required attributes {!r}".format(", ".join(repr(k) for k in missing))
            raise RuntimeError(error)

        return initial_values

    def get_update_values(self, updates, state_reader=None):
        # type: (Mapping[str, Any], SupportsKeysAndGetItem | None) -> tuple[dict[str, Any], dict[str, Any]]

        # Compile update values.
        delegate_self = DelegateSelf(self, state_reader)
        sorting_key = lambda i: len(self[i[0]].recursive_dependencies)
        for name, value in sorted(six.iteritems(updates), key=sorting_key, reverse=True):
            setattr(delegate_self, name, value)
        new_values, old_values = delegate_self.__.get_results()

        # Ensure no required attributes are being deleted.
        for name, value in six.iteritems(new_values):
            if value is DELETED and self[name].required:
                error = "can't delete required attribute {!r}".format(name)
                raise AttributeError(error)

        return new_values, old_values


@runtime_final.final
class StateReader(Base):
    __slots__ = ("__instance",)

    def __init__(self, instance=None):
        # type: (ClassProtocol | None) -> None
        self.__instance = instance

    def __getitem__(self, name):
        if self.instance is not None:
            try:
                return self.instance[name]
            except KeyError:
                pass
        raise KeyError(name)

    def keys(self):
        if self.instance is not None:
            for name in self.instance:
                yield name

    @property
    def instance(self):
        # type: () -> ClassProtocol | None
        return self.__instance


@runtime_final.final
class DelegateSelf(Base):
    """Intermediary self object provided to delegates."""

    __slots__ = ("__",)

    def __init__(self, attribute_map, state=None):
        # type: (AttributeMap, SupportsKeysAndGetItem | None) -> None
        """
        :param attribute_map: Attribute map.
        :param state: State/state reader.
        """
        if state is None:
            state = StateReader()
        internals = _DelegateSelfInternals(self, attribute_map, state)  # noqa
        object.__setattr__(self, "__", internals)

    def __dir__(self):
        # type: () -> list[str]
        """
        Get attribute names.

        :return: Attribute names.
        """
        if self.__.in_getter is not None:
            attribute = self.__.in_getter
            return sorted(n for n, a in six.iteritems(self.__.attribute_map) if a is attribute or a in a.dependencies)
        return sorted(self.__.attribute_map)

    def __getattr__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.
        :param name: Attribute name.
        :return: Value.
        """
        if name != "__" and name in self.__.attribute_map:
            return self[name]
        else:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.
        :param name: Attribute name.
        :param value: Value.
        """
        if name in self.__.attribute_map:
            self[name] = value
        else:
            super(DelegateSelf, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.
        :param name: Attribute name.
        """
        if name in self.__.attribute_map:
            del self[name]
        else:
            super(DelegateSelf, self).__delattr__(name)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.
        :param name: Attribute name.
        :return: Value.
        """
        return self.__.get_value(name)

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.
        :param name: Attribute name.
        :param value: Value.
        """
        self.__.set_value(name, value)

    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.
        :param name: Attribute name.
        """
        self.__.delete_value(name)


@runtime_final.final
class _DelegateSelfInternals(Base):
    """Internals for :class:`DelegateSelf`."""

    __slots__ = (
        "__iobj_ref",
        "__attribute_map",
        "__state",
        "__dependencies",
        "__in_getter",
        "__new_values",
        "__old_values",
        "__dirty",
    )

    def __init__(self, iobj, attribute_map, state):
        # type: (DelegateSelf, AttributeMap, SupportsKeysAndGetItem) -> None
        """
        :param iobj: Internal object.
        :param attribute_map: Attribute map.
        :param state: State.
        """
        self.__iobj_ref = weakref.ref(iobj)
        self.__attribute_map = attribute_map
        self.__state = state
        self.__dependencies = None  # type: tuple[Attribute, ...] | None
        self.__in_getter = None  # type: Attribute | None
        self.__new_values = {}  # type: dict[str, Any]
        self.__old_values = {}  # type: dict[str, Any]
        self.__dirty = set(attribute_map).difference(state.keys())  # type: set[str]

    def get_value(self, name):
        """
        Get current value for attribute.

        :param name: Attribute name.
        :return: Value.
        :raises NameError: Can't access attribute not declared as dependency.
        :raises AttributeError: Attribute has no value.
        """
        attribute = self.__get_attribute(name)
        if self.__dependencies is not None and attribute not in self.__dependencies:
            error = (
                "can't access {!r} attribute from {!r} getter delegate since it was " "not declared as a dependency"
            ).format(name, self.__in_getter.name)
            raise NameError(error)

        if name in self.__dirty:
            value = MISSING
        else:
            try:
                value = self.__new_values[name]
            except KeyError:
                try:
                    value = self.__state[name]
                except KeyError:
                    value = MISSING

        if value in (MISSING, DELETED):
            if attribute.delegated:
                with self.__getter_context(attribute):
                    value = attribute.fget(self.iobj)
                value = attribute.process(value)
                self.__set_new_value(name, value)
                return value
            else:
                error = "attribute {!r} has no value".format(name)
                raise AttributeError(error)
        else:
            return value

    def set_value(self, name, value, process=True):
        # type: (str, Any, bool) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :param process: Whether to process value or not.
        :raises AttributeError: Can't set attributes while running getter delegate.
        :raises AttributeError: Attribute is read-only.
        :raises AttributeError: Attribute already has a value and can't be changed.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if value is DELETED:
            self.delete_value(name)
            return

        if self.__in_getter is not None:
            error = "can't set attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.updatable:
            if attribute.delegated:
                error = "attribute {!r} is read-only".format(name)
                raise AttributeError(error)
            try:
                self.get_value(name)
            except AttributeError:
                pass
            else:
                error = "attribute {!r} already has a value and can't be changed".format(name)
                raise AttributeError(error)

        if process:
            value = attribute.process(value)
        if attribute.delegated:
            attribute.fset(self.iobj, value)
        else:
            self.__set_new_value(name, value)

    def delete_value(self, name):
        """
        Delete attribute.

        :param name: Attribute name.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """
        if self.__in_getter is not None:
            error = "can't delete attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.deletable:
            error = "attribute {!r} is not deletable".format(name)
            raise AttributeError(error)

        if attribute.delegated:
            attribute.fdel(self.iobj)
        else:
            self.get_value(name)  # will error if it has no value, which we want
            self.__set_new_value(name, DELETED)

    @contextlib.contextmanager
    def __getter_context(self, attribute):
        # type: (Attribute) -> Iterator
        """
        Getter context.

        :param attribute: Attribute.
        :return: Getter context manager.
        """
        before = self.__in_getter
        before_dependencies = self.__dependencies

        self.__in_getter = attribute
        if attribute.delegated:
            self.__dependencies = attribute.dependencies
        else:
            self.__dependencies = None

        try:
            yield
        finally:
            self.__in_getter = before
            self.__dependencies = before_dependencies

    def __set_new_value(self, name, value):
        # type: (str, Any) -> None
        """
        Set new attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        try:
            old_value = self.__state[name]
        except KeyError:
            old_value = DELETED

        if value is not old_value:
            self.__old_values[name] = old_value
            self.__new_values[name] = value
        else:
            self.__old_values.pop(name, None)
            self.__new_values.pop(name, None)

        self.__dirty.discard(name)
        for dependent in self.__attribute_map[name].recursive_dependents:
            self.__dirty.add(dependent.name)
            try:
                old_value = self.__state[dependent.name]
            except KeyError:
                self.__new_values.pop(dependent.name, None)
                self.__old_values.pop(dependent.name, None)
            else:
                self.__old_values[dependent.name] = old_value
                self.__new_values[dependent.name] = DELETED

    def __get_attribute(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        :raises AttributeError: Has no such attribute.
        """
        try:
            return self.__attribute_map[name]
        except KeyError:
            pass
        error = "no attribute named {!r}".format(name)
        raise AttributeError(error)

    def get_results(self):
        # type: () -> tuple[dict[str, Any], dict[str, Any]]
        """
        Get results.

        :return: New values, old values.
        """
        sorted_dirty = sorted(
            self.__dirty,
            key=lambda n: len(self.__attribute_map[n].recursive_dependencies),
        )
        failed = set()
        success = set()
        for name in sorted_dirty:
            try:
                self.get_value(name)
            except AttributeError:
                failed.add(name)
            else:
                success.add(name)

        new_values = self.__new_values.copy()
        old_values = self.__old_values.copy()

        return new_values, old_values

    @property
    def iobj(self):
        # type: () -> DelegateSelf | None
        """Intermediary object."""
        return self.__iobj_ref()

    @property
    def attribute_map(self):
        # type: () -> AttributeMap
        """AttributeMap."""
        return self.__attribute_map

    @property
    def state(self):
        # type: () -> SupportsKeysAndGetItem
        """State."""
        return self.__state

    @property
    def in_getter(self):
        # type: () -> Attribute | None
        """Whether running in an attribute's getter delegate."""
        return self.__in_getter


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


def _traverse(attribute, direction):
    # type: (Attribute, Literal["dependencies", "dependents"]) -> tuple[Attribute, ...]
    unvisited = set(getattr(attribute, direction))  # type: set[Attribute]
    visited = set()  # type: set[Attribute]
    while unvisited:
        dep = unvisited.pop()
        if dep in visited:
            continue
        visited.add(dep)
        for sub_dep in getattr(dep, direction):
            unvisited.add(sub_dep)
    return tuple(sorted(visited, key=lambda d: d.order))
