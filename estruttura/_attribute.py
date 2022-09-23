import collections

import six
from basicco import custom_repr, runtime_final, recursive_repr, fabricate_value, namespace
from tippo import Any, Callable, TypeVar, Iterable, Generic, TypeAlias, Type, Tuple, Mapping, Protocol, Literal, MutableMapping, overload, cast

from ._constants import SupportsKeysAndGetItem, MissingType, MISSING, DELETED, DEFAULT
from ._dict import BaseDict, BaseMutableDict
from ._bases import Base, BaseHashable
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

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("default", self.default),
            ("factory", self.factory),
            ("required", self.required),
            ("init", self.init),
            ("updatable", self.updatable),
            ("deletable", self.deletable),
            ("delegated", self.delegated),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("relationship", self.relationship),
            ("dependencies", self.dependencies),
            ("dependents", self.dependents),
            ("fget", self.fget),
            ("fset", self.fset),
            ("fdel", self.fdel),
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

    def getter(self, *dependencies):
        # type: (A, *Attribute) -> Callable[[Callable[[ClassProtocol], T_co]], A]
        """
        Define a getter delegate method by using a decorator.

        :param dependencies: Attribute dependencies.
        :return: Getter method decorator.
        :raises ValueError: Cannot define a getter for a non-delegated attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Getter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """

        def decorator(func):
            # type: (Callable[[ClassProtocol], T_co]) -> A
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.fget is not None:
                error = "getter delegate already defined"
                raise ValueError(error)
            assert not self._dependencies

            for dependency in dependencies:
                if dependency.owned:
                    error = "dependency attribute {!r} already named and owned by a class".format(dependency.name)
                    raise ValueError(error)
                dependency._dependents += (self,)  # noqa

            self._dependencies = dependencies
            self._fget = func
            return self

        return decorator

    def setter(self):
        # type: (A) -> Callable[[Callable[[ClassProtocol, T_co], None]], A]
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

        def decorator(func):
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

        return decorator

    def deleter(self):
        # type: (A) -> Callable[[Callable[[ClassProtocol], None]], A]
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

        def decorator(func):
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

        return decorator

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
        internal_names = set()
        initial_values = {}  # type: dict[str, Any]
        for name, attribute in six.iteritems(self):

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

                elif attribute.required:

                    # Keep track of non-init, required attribute names (internal attributes).
                    internal_names.add(name)

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
        initial_values = self.get_update_values(initial_values)

        # Check for required internal attributes.
        missing = internal_names.difference(initial_values)
        if missing:
            error = "missing values for internal required attributes {!r}".format(", ".join(repr(k) for k in missing))
            raise RuntimeError(error)

        return initial_values

    def get_update_values(self, updates, value_getter=None):
        updates = dict(updates)
        state = {}
        compiled_updates = {}

        def callback(name):
            try:
                _ = self[name]
            except KeyError:
                error = "no attribute named {!r}".format(name)
                raise AttributeError(error)
            if name in state:
                error = "attribute {!r} was not declared as a getter dependency".format(name)
                raise AttributeError(error)
            if value_getter is not None:
                value = value_getter(name)
                if value is not MISSING:
                    state[name] = value
                    return True
            while name not in state and updates:
                update(*updates.popitem())
            return name in state

        def set_value(name, value):
            if name in compiled_updates:
                error = "attribute {!r} can't be set more than once".format(name)
                raise AttributeError(error)
            attribute = self[name]
            delete = value is DELETED
            if not delete:
                state[name] = compiled_updates[name] = attribute.process(value)
                print("set_value", name, value)
            else:
                del state[name]
                compiled_updates[name] = DELETED
                print("delete_value", name)
            for dependent in attribute.recursive_dependents:
                dependent_state = FilteredDict(state, {a.name for a in dependent.dependencies})
                lazy_namespace = LazyNamespace(dependent_state, callback)
                value = attribute.process(dependent.fget(lazy_namespace))
                state[dependent.name] = compiled_updates[dependent.name] = value
                print("set_dependent_value", dependent.name, compiled_updates[dependent.name])

        lazy_mutable_namespace = LazyMutableNamespace(SetterDict(state, set_value), callback)

        def update(name, value):
            attribute = self[name]
            delete = value is DELETED
            if not attribute.delegated:
                if not delete:
                    if attribute.updatable or name not in state:
                        set_value(name, value)
                        return
                elif attribute.deletable:
                    if name not in state and not callback(name):
                        error = "no value set for attribute {!r}".format(name)
                        raise AttributeError(error)
                    set_value(name, value)

            elif attribute.fset is not None:
                if not delete:
                    attribute.fset(lazy_mutable_namespace, value)
                    print("running setter", name)
                    return
                elif attribute.deletable:
                    attribute.fdel(lazy_mutable_namespace)
                    print("running deleter", name)
                    return

            error = "attribute {!r} is not {}".format(name, "deletable" if delete else "updatable")
            raise AttributeError(error)

        while updates:
            update(*updates.popitem())

        print("COMPILED UPDATES", compiled_updates)
        return compiled_updates


class LazyNamespace(namespace.Namespace[Any]):
    __slots__ = ("__callback__",)

    def __init__(self, wrapped=None, callback=None):
        # type: (Mapping[str, Any] | namespace.Namespace[Any] | None, Callable[[str], bool]) -> None
        super(LazyNamespace, self).__init__(wrapped=wrapped)
        self.__callback__ = callback

    def __getattr__(self, name):
        if self.__callback__(name):
            return self.__getattribute__(name)
        else:
            error = "no attribute named {!r}".format(name)
            raise AttributeError(error)


class LazyMutableNamespace(LazyNamespace, namespace.MutableNamespace[Any]):
    __slots__ = ()


class FilteredDict(BaseDict[str, Any]):
    __slots__ = ("__wrapped", "__allowed_keys")
    __hash__ = None  # type: ignore

    def __init__(self, wrapped, allowed_keys):
        self.__wrapped = wrapped
        self.__allowed_keys = allowed_keys

    def __repr__(self):
        return repr(dict(self))

    def __eq__(self, other):
        return isinstance(other, Mapping) and dict(self) == dict(other)

    def __getitem__(self, name):
        if name not in self.__allowed_keys:
            raise KeyError(name)
        return self.__wrapped[name]

    def __contains__(self, name):
        return name in self.__allowed_keys and name in self.__wrapped

    def get(self, name, fallback=None):
        if name not in self.__allowed_keys:
            return fallback
        return self.__wrapped.get(name, fallback)

    def iteritems(self):
        for name, attribute in six.iteritems(self.__wrapped):
            if name not in self.__allowed_keys:
                continue
            yield (name, attribute)

    def iterkeys(self):
        for name in six.iterkeys(self.__wrapped):
            if name not in self.__allowed_keys:
                continue
            yield name

    def itervalues(self):
        for name, attribute in six.iteritems(self.__wrapped):
            if name not in self.__allowed_keys:
                continue
            yield attribute

    def __len__(self):
        return len(self.__allowed_keys.intersection(self.__wrapped))

    def __iter__(self):
        for name in six.iterkeys(self.__wrapped):
            if name not in self.__allowed_keys:
                continue
            yield name


class SetterDict(MutableMapping[str, Any]):
    __slots__ = ("__wrapped", "__setter")
    __hash__ = None  # type: ignore

    def __init__(self, wrapped, setter):
        self.__wrapped = wrapped
        self.__setter = setter

    def __getitem__(self, name):
        return self.__wrapped[name]

    def __setitem__(self, name, value):
        self.__setter(name, value)

    def __delitem__(self, name):
        self.__setter(name, DELETED)

    def __len__(self):
        return len(self.__wrapped)

    def __iter__(self):
        for name in six.iterkeys(self.__wrapped):
            yield name


def _traverse(attribute, direction):
    # type: (Attribute, Literal["dependencies", "dependents"]) -> tuple[Attribute, ...]
    unvisited = dict((id(d), d) for d in getattr(attribute, direction))
    visited = {}
    while unvisited:
        dep_id, dep = unvisited.popitem()
        if dep_id in visited:
            continue
        visited[dep_id] = dep
        for sub_dep in getattr(dep, direction):
            unvisited[id(sub_dep)] = sub_dep
    return tuple(sorted(six.itervalues(visited), key=lambda d: d.order))
