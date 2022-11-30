"""Attribute descriptors."""

import six
from basicco import basic_data, fabricate_value, unique_iterator
from basicco.namespace import Namespace
from basicco.runtime_final import final
from tippo import (
    Any,
    Callable,
    Generic,
    Iterable,
    Literal,
    Mapping,
    SupportsGetItem,
    SupportsGetSetDeleteItem,
    SupportsKeysAndGetItem,
    Type,
    TypeVar,
    cast,
    overload,
)

from ._relationship import Relationship
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

_attribute_count = 0


# noinspection PyAbstractClass
class Attribute(basic_data.ImmutableBasicData, Generic[T_co]):
    """Attribute descriptor."""

    __slots__ = (
        "_owner",
        "_name",
        "_default",
        "_factory",
        "_relationship",
        "_required",
        "_init",
        "_init_as",
        "_settable",
        "_deletable",
        "_serializable",
        "_serialize_as",
        "_serialize_default",
        "_constant",
        "_repr",
        "_eq",
        "_order",
        "_hash",
        "_doc",
        "_metadata",
        "_namespace",
        "_callback",
        "_extra_paths",
        "_builtin_paths",
        "_processed_default",
        "_dependencies",
        "_recursive_dependencies",
        "_dependents",
        "_recursive_dependents",
        "_fget",
        "_fset",
        "_fdel",
        "_count",
    )

    def __init__(
        self,  # type: A
        default=MISSING,  # type: T_co | MissingType
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        relationship=Relationship(),  # type: Relationship[T_co]
        required=None,  # type: bool | None
        init=None,  # type: bool | None
        init_as=None,  # type: A | str | None
        settable=None,  # type: bool | None
        deletable=None,  # type: bool | None
        serializable=None,  # type: bool | None
        serialize_as=None,  # type: A | str | None
        serialize_default=True,  # type: bool
        constant=False,  # type: bool
        repr=None,  # type: bool | Callable[[T_co], str] | None
        eq=None,  # type: bool | None
        order=None,  # type: bool | None
        hash=None,  # type: bool | None
        doc="",  # type: str
        metadata=None,  # type: Any
        namespace=None,  # type: Namespace | Mapping[str, Any] | None
        callback=None,  # type: Callable[[A], None] | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param default: Default value.
        :param factory: Default factory.
        :param relationship: Relationship.
        :param required: Whether it is required to have a value.
        :param init: Whether to include in the `__init__` method.
        :param init_as: Alternative attribute or name to use when initializing.
        :param settable: Whether the value can be changed after being set.
        :param deletable: Whether the value can be deleted.
        :param serializable: Whether it's serializable.
        :param serialize_as: Alternative attribute or name to use when serializing.
        :param serialize_default: Whether to serialize default value.
        :param constant: Whether attribute is a class constant.
        :param repr: Whether to include in the `__repr__` method (or a custom repr function).
        :param eq: Whether to include in the `__eq__` method.
        :param order: Whether to include in the `__lt__`, `__le__`, `__gt__`, `__ge__` methods.
        :param hash: Whether to include in the `__hash__` method.
        :param doc: Documentation.
        :param metadata: User metadata.
        :param namespace: Namespace.
        :param callback: Callback that runs after attribute has been named/owned by class.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        global _attribute_count

        # Resolve/check parameters based on whether attribute is a constant.
        if constant:

            if default is MISSING:
                error = "constant attribute needs a default value"
                raise ValueError(error)

            if factory is not MISSING:
                error = "constant attribute can't have a default factory"
                raise ValueError(error)

            if required is None:
                required = False
            elif required:
                error = "constant attribute can't be required"
                raise ValueError(error)

            if init is None:
                init = False
            elif init:
                error = "constant attribute can't be in init"
                raise ValueError(error)

            if settable is None:
                settable = False
            elif settable:
                error = "constant attribute can't be settable"
                raise ValueError(error)

            if deletable is None:
                deletable = False
            elif deletable:
                error = "constant attribute can't be deletable"
                raise ValueError(error)

            if serializable is None:
                serializable = False
            elif serializable:
                error = "constant attribute can't be serializable"
                raise ValueError(error)

            if repr is None:
                repr = False
            elif repr:
                error = "constant attribute can't be in repr"
                raise ValueError(error)

            if eq is None:
                eq = False
            elif eq:
                error = "constant attribute can't be in eq"
                raise ValueError(error)

            if order is None:
                order = False
            elif order:
                error = "constant attribute can't be ordered"
                raise ValueError(error)

            if hash is None:
                hash = False
            elif hash:
                error = "constant attribute can't be in hash"
                raise ValueError(error)

        # Not a constant, set default parameter values.
        else:

            if required is None:
                required = True

            if repr is None:
                repr = True

            if eq is None:
                eq = True

        # Ensure single default source.
        if default is not MISSING and factory is not MISSING:
            error = "can't declare both 'default' and 'factory'"
            raise ValueError(error)

        # Ensure default is set when not serializing it.
        if not serialize_default and default is MISSING:
            error = "'default' value is required when 'serialize_default' is set to False"
            raise ValueError(error)

        # Ensure safe hash.
        if hash is None:
            hash = eq
        if hash and not eq:
            error = "can't contribute to the hash if it's not contributing to the eq"
            raise ValueError(error)

        # Ensure safe order.
        if order is None:
            order = False
        if order and not eq:
            error = "can't contribute to order if it's not contributing to the eq"
            raise ValueError(error)
        if order and not required:
            error = "can't contribute to order if it's not required"
            raise ValueError(error)

        # Set attributes.
        self._owner = None  # type: Type[SupportsGetItem] | None
        self._name = None  # type: str | None

        self._default = default
        self._factory = factory
        self._relationship = relationship
        self._required = bool(required)
        self._init = bool(init) if init is not None else None
        self._init_as = init_as
        self._settable = bool(settable) if settable is not None else None
        self._deletable = bool(deletable) if deletable is not None else None
        self._serializable = bool(serializable) if serializable is not None else None
        self._serialize_as = serialize_as
        self._serialize_default = bool(serialize_default)
        self._constant = bool(constant)
        self._dependencies = ()  # type: tuple[Attribute, ...]
        self._repr = repr if callable(repr) else bool(repr)  # type: bool | Callable[[T_co], str]
        self._eq = bool(eq)
        self._order = bool(order)
        self._hash = bool(hash)
        self._doc = doc
        self._metadata = metadata
        self._namespace = Namespace(namespace if namespace is not None else {})  # type: Namespace
        self._callback = callback
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        self._processed_default = False  # type: bool
        self._recursive_dependencies = None  # type: tuple[Attribute, ...] | None
        self._dependents = ()  # type: tuple[Attribute, ...]
        self._recursive_dependents = None  # type: tuple[Attribute, ...] | None
        self._fget = None  # type: Callable[[Any], T_co] | None
        self._fset = None  # type: Callable[[Any, T_co], None] | None
        self._fdel = None  # type: Callable[[Any], None] | None

        # Increment global count.
        _attribute_count += 1
        self._count = _attribute_count

    @final
    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, None) -> A
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (A, None, Type) -> A | T_co
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (object, Type) -> T_co
        pass

    def __get__(self, instance, owner):

        # Constant value.
        if owner is not None and self.constant:
            return self.default

        # Instance value.
        if instance is not None:
            if self.name is None:
                assert self.owner is None
                error = "attribute not named/owned"
                raise RuntimeError(error)
            return cast(SupportsGetItem, instance)[self.name]

        return self

    def __set_name__(self, owner, name):
        # type: (Type[SupportsGetItem], str) -> None

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
            if self.settable is None:
                self._settable = self.fset is not None
            if self.deletable is None:
                self._deletable = self.fdel is not None
            if self.init is None:
                self._init = self.settable
        else:
            if self.settable is None:
                self._settable = True
            if self.deletable is None:
                self._deletable = False
            if self.init is None:
                self._init = True

        if self._serializable is None:
            self._serializable = self._init or self.settable

        assert not any(
            p is None
            for p in (
                self._settable,
                self._deletable,
                self._init,
                self._serializable,
            )
        )

        # More checks.
        if self.delegated:
            if self.fset is None and self.init:
                error = "delegated attribute {!r} is in __init__ but has no setter delegate was defined".format(name)
                raise TypeError(error)
            if self.fset is None:
                if self.settable:
                    error = "delegated attribute {!r} is settable but has no setter delegate was defined".format(name)
                    raise TypeError(error)
                if self.has_default:
                    error = "delegated attribute {!r} has no setter but has a default".format(name)
                    raise TypeError(error)
            if self.fdel is None and self.deletable:
                error = "delegated attribute {!r} is deletable but has no deleter delegate was defined".format(name)
                raise TypeError(error)

        if not self.serializable:
            if self.serialize_as is not None:
                error = "attribute {!r} can't set 'serialize_as' when 'serializable' is False".format(name)
                raise TypeError(error)

        if not self.init:
            if self.init_as is not None:
                error = "attribute {!r} can't set 'init_as' when 'init' is False".format(name)
                raise TypeError(error)

        # Set owner and name.
        self._owner = owner
        self._name = name

    def __run_callback__(self):
        # type: (A) -> None
        assert self.owned
        assert self.named
        if self._callback is not None:
            self._callback(self)

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
        """
        Convert to items.

        :param usecase: Use case.
        :return: Items.
        """
        items = [
            ("default", self.default),
            ("factory", self.factory),
            ("required", self.required),
            ("init", self.init),
            ("init_as", self.init_as),
            ("settable", self.settable),
            ("deletable", self.deletable),
            ("serializable", self.serializable),
            ("serialize_as", self.serialize_as),
            ("serialize_default", self.serialize_default),
            ("constant", self.constant),
            ("repr", self.repr),
            ("eq", self.eq),
            ("order", self.order),
            ("hash", self.hash),
            ("doc", self.doc),
            ("metadata", self.metadata),
            ("namespace", self.namespace),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        ]
        if usecase is not basic_data.ItemUsecase.INIT:
            items.extend(
                [
                    ("name", self.name),
                    ("owner", self.owner),
                    ("delegated", self.delegated),
                    ("count", self.count),
                ]
            )
            if usecase is not basic_data.ItemUsecase.REPR:
                items.extend(
                    [
                        ("callback", self._callback),
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

    def get_default_value(self):
        # type: () -> T_co
        """
        Get default value.

        :return: Default value.
        :raises RuntimeError: No valid default value/factory defined.
        """
        if self.default is not MISSING:
            default_value = self.default
        elif self.factory is not MISSING:
            default_value = fabricate_value.fabricate_value(
                self.factory,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            error = "no valid default/factory defined"
            raise RuntimeError(error)
        return default_value

    def process_value(self, value, location=MISSING):
        # type: (Any, Any) -> T_co
        """
        Process value (convert, check type, validate).

        :param value: Value.
        :param location: Optional value location information.
        :return: Processed value.
        :raises ProcessingError: Error while processing value.
        """
        if location is MISSING and self.named:
            location = self.name
        try:
            return self.relationship.process_value(value, location)
        except Exception as e:
            exc = type(e)(e)
            six.raise_from(exc, None)
            raise exc

    @overload
    def getter(self, maybe_func):
        # type: (A, Callable[[Any], T_co]) -> A
        """."""

    @overload
    def getter(self, *dependencies):
        # type: (A, *Attribute) -> Callable[[Callable[[Any], T_co]], A]
        """."""

    def getter(self, *dependencies):
        """
        Define a getter delegate method by using a decorator.

        :param dependencies: Attribute dependencies.
        :return: Getter method decorator.
        :raises RuntimeError: Can't define a delegate for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Getter delegate already defined.
        """
        if self.constant:
            error_ = "can't define a delegate for a constant attribute"
            raise RuntimeError(error_)

        def getter_decorator(func):
            """Getter decorator."""
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
        # type: (A, None) -> Callable[[Callable[[Any, T_co], None]], A]
        """."""

    @overload
    def setter(self, maybe_func):
        # type: (A, Callable[[Any, T_co], None]) -> A
        """."""

    def setter(self, maybe_func=None):
        """
        Define a setter delegate method by using a decorator.

        :return: Setter method decorator.
        :raises RuntimeError: Can't define a delegate for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not settable.
        :raises ValueError: Need to define a getter before defining a setter.
        :raises ValueError: Setter delegate already defined.
        """
        if self.constant:
            error_ = "can't define a delegate for a constant attribute"
            raise RuntimeError(error_)

        def setter_decorator(func):
            """Setter decorator."""
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.settable is False:
                error = "attribute is not settable, can't define setter delegate"
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
        # type: (A, None) -> Callable[[Callable[[SupportsGetItem], None]], A]
        """."""

    @overload
    def deleter(self, maybe_func):
        # type: (A, Callable[[SupportsGetItem], None]) -> A
        """."""

    def deleter(self, maybe_func=None):
        """
        Define a deleter delegate method by using a decorator.

        :return: Deleter method decorator.
        :raises RuntimeError: Can't define a delegate for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not deletable.
        :raises ValueError: Need to define a getter before defining a deleter.
        :raises ValueError: Deleter delegate already defined.
        """
        if self.constant:
            error_ = "can't define a delegate for a constant attribute"
            raise RuntimeError(error_)

        def deleter_decorator(func):
            """Deleter decorator."""
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

    @overload
    def update(self, __m, **kwargs):
        # type: (A, SupportsKeysAndGetItem[str, Any], **Any) -> A
        """."""

    @overload
    def update(self, __m, **kwargs):
        # type: (A, Iterable[tuple[str, Any]], **Any) -> A
        """."""

    @overload
    def update(self, **kwargs):
        # type: (A, **Any) -> A
        """."""

    def update(self, *args, **kwargs):
        """
        Make a new attribute with updates.

        :params: Same parameters as :class:`dict`.
        :return: Updated attribute.
        """
        init_args = self.to_dict(basic_data.ItemUsecase.INIT)
        init_args.update(*args, **kwargs)
        return cast(A, type(self)(**init_args))

    @property
    def name(self):
        # type: () -> str | None
        """Attribute name."""
        return self._name

    @property
    def owner(self):
        # type: () -> Type[SupportsGetItem] | None
        """Owner class."""
        return self._owner

    @property
    def default(self):
        # type: () -> T_co | MissingType
        """Default value."""
        if not self._processed_default:
            if self._default is not MISSING:
                self._default = self.process_value(self._default)
            self._processed_default = True
        return self._default

    @property
    def factory(self):
        # type: () -> Callable[..., T_co] | str | MissingType
        """Default factory."""
        return self._factory

    @property
    def relationship(self):
        # type: () -> Relationship[T_co]
        """Relationship."""
        return self._relationship

    @property
    def required(self):
        # type: () -> bool
        """Whether it is required to have a value."""
        return self._required

    @property
    def init(self):
        # type: () -> bool | None
        """Whether to include in the `__init__` method."""
        return self._init

    @property
    def init_as(self):
        # type: (A) -> A | str | None
        """Alternative attribute or name to use when initializing."""
        return self._init_as

    @property
    def settable(self):
        # type: () -> bool | None
        """Whether the value can be changed after being set."""
        return self._settable

    @property
    def deletable(self):
        # type: () -> bool | None
        """Whether the value can be deleted."""
        return self._deletable

    @property
    def serializable(self):
        # type: () -> bool | None
        """Whether it's serializable."""
        return self._serializable

    @property
    def serialize_as(self):
        # type: (A) -> A | str | None
        """Alternative attribute or name to use when serializing."""
        return self._serialize_as

    @property
    def serialize_default(self):
        # type: () -> bool | None
        """Whether to serialize default value."""
        return self._serialize_default

    @property
    def constant(self):
        # type: () -> bool
        """Whether attribute is a class constant."""
        return self._constant

    @property
    def repr(self):
        # type: () -> bool | Callable[[T_co], str]
        """Whether to include in the `__repr__` method (or a custom repr function)."""
        return self._repr

    @property
    def eq(self):
        # type: () -> bool
        """Whether to include in the `__eq__` method."""
        return self._eq

    @property
    def order(self):
        # type: () -> bool
        """Whether to include in the `__lt__`, `__le__`, `__gt__`, `__ge__` methods."""
        return self._order

    @property
    def hash(self):
        # type: () -> bool
        """Whether to include in the `__hash__` method."""
        return self._hash

    @property
    def doc(self):
        # type: () -> str
        """Documentation."""
        return self._doc

    @property
    def metadata(self):
        # type: () -> Any
        """User metadata."""
        return self._metadata

    @property
    def namespace(self):
        # type: () -> Namespace
        """Namespace."""
        return self._namespace

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
    def dependencies(self):
        # type: () -> tuple[Attribute, ...]
        """Getter dependencies."""
        return self._dependencies

    @property
    def recursive_dependencies(self):
        # type: () -> tuple[Attribute, ...]
        """Recursive getter dependencies."""
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
        """Dependents."""
        return self._dependents

    @property
    def recursive_dependents(self):
        # type: () -> tuple[Attribute, ...]
        """Recursive dependents."""
        if self._recursive_dependents is not None:
            return self._recursive_dependents
        recursive_dependents = _traverse(self, direction="dependents")

        # Cache only if already owned.
        if self.owned:
            self._recursive_dependents = recursive_dependents

        return recursive_dependents

    @property
    def fget(self):
        # type: () -> Callable[[Any], T_co] | None
        """Getter function."""
        return self._fget

    @property
    def fset(self):
        # type: () -> Callable[[Any, T_co], None] | None
        """Setter function."""
        return self._fset

    @property
    def fdel(self):
        # type: () -> Callable[[Any], None] | None
        """Deleter function."""
        return self._fdel

    @property
    def count(self):
        # type: () -> int
        """Global count number for this attribute."""
        return self._count

    @property
    def owned(self):
        # type: () -> bool
        """Whether attribute is owned by a class or not."""
        owned = self._owner is not None
        assert owned is (self._name is not None)
        return owned

    @property
    def named(self):
        # type: () -> bool
        """Whether attribute is named by a class or not."""
        named = self._name is not None
        assert named is (self._owner is not None)
        return named

    @property
    def delegated(self):
        # type: () -> bool
        """Whether attribute has at least a getter delegate."""
        return any(d is not None for d in (self.fget, self.fset, self.fdel))

    @property
    def has_default(self):
        # type: () -> bool
        """Whehter attribute has a default value/default factory."""
        return self._default is not MISSING or self._factory is not MISSING


A = TypeVar("A", bound=Attribute)  # attribute self type


class MutableAttribute(Attribute[T]):
    """Mutable attribute descriptor."""

    __slots__ = ()

    def __set__(self, instance, value):
        # type: (object, T) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)

        if self.constant:
            error = "can't change constant class attribute {!r}".format(self.name)
            raise AttributeError(error)

        cast(SupportsGetSetDeleteItem, instance)[self.name] = value

    def __delete__(self, instance):
        # type: (object) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)

        if self.constant:
            error = "can't delete constant class attribute {!r}".format(self.name)
            raise AttributeError(error)

        del cast(SupportsGetSetDeleteItem, instance)[self.name]


MA = TypeVar("MA", bound=MutableAttribute)  # mutable attribute self type


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
    return tuple(sorted(visited, key=lambda d: d.count))


def getter(attribute, dependencies=()):
    # type: (T, Iterable) -> Callable[[Callable[[Any], T]], None]
    """
    Decorator that sets a getter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param attribute: Attribute.
    :param dependencies: Dependencies.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any], T]) -> None
        """Getter decorator."""
        if func.__name__ != "_":
            error = "getter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], attribute).getter(*dependencies)(func)

    return decorator


def setter(attribute):
    # type: (T) -> Callable[[Callable[[Any, T], None]], None]
    """
    Decorator that sets a setter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param attribute: Attribute.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any, T], None]) -> None
        """Setter decorator."""
        if func.__name__ != "_":
            error = "setter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], attribute).setter(func)

    return decorator


def deleter(attribute):
    # type: (T) -> Callable[[Callable[[Any], None]], None]
    """
    Decorator that sets a deleter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param attribute: Attribute.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any], None]) -> None
        """Deleter decorator."""
        if func.__name__ != "_":
            error = "deleter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], attribute).deleter(func)

    return decorator
