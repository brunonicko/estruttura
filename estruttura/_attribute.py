import six
from basicco.basic_data import ImmutableBasicData, ItemUsecase
from basicco.unique_iterator import unique_iterator
from basicco.fabricate_value import fabricate_value
from tippo import (
    Any,
    Callable,
    Type,
    TypeVar,
    Iterable,
    Generic,
    Literal,
    SupportsGetItem,
    SupportsKeysAndGetItem,
    SupportsGetSetDeleteItem,
    cast,
    overload,
)

from .constants import MissingType, MISSING
from ._relationship import Relationship


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

RT = TypeVar("RT", bound=Relationship)

_attribute_count = 0


# noinspection PyAbstractClass
class StructureAttribute(ImmutableBasicData, Generic[T_co, RT]):
    __slots__ = (
        "_owner",
        "_name",
        "_default",
        "_factory",
        "_relationship",
        "_required",
        "_init",
        "_updatable",
        "_deletable",
        "_constant",
        "_repr",
        "_eq",
        "_order",
        "_hash",
        "_metadata",
        "_extra_paths",
        "_builtin_paths",
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
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        relationship=None,  # type: RT | None
        required=None,  # type: bool | None
        init=None,  # type: bool | None
        updatable=None,  # type: bool | None
        deletable=None,  # type: bool | None
        constant=False,  # type: bool
        repr=None,  # type: bool | None
        eq=None,  # type: bool | None
        order=None,  # type: bool | None
        hash=None,  # type: bool | None
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        global _attribute_count

        if constant:

            # Resolve/check parameters based on whether attribute is a constant.
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

            if updatable is None:
                updatable = False
            elif updatable:
                error = "constant attribute can't be updatable"
                raise ValueError(error)

            if deletable is None:
                deletable = False
            elif deletable:
                error = "constant attribute can't be deletable"
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

        else:

            # Not a constant, set default parameter values.
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
        self._updatable = bool(updatable) if updatable is not None else None
        self._deletable = bool(deletable) if deletable is not None else None
        self._constant = bool(constant)
        self._dependencies = ()  # type: tuple[StructureAttribute, ...]
        self._repr = bool(repr)
        self._eq = bool(eq)
        self._order = bool(order)
        self._hash = bool(hash)
        self._metadata = metadata
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        self._recursive_dependencies = None  # type: tuple[StructureAttribute, ...] | None
        self._dependents = ()  # type: tuple[StructureAttribute, ...]
        self._recursive_dependents = None  # type: tuple[StructureAttribute, ...] | None
        self._fget = None  # type: Callable[[SupportsGetItem], T_co] | None
        self._fset = None  # type: Callable[[SupportsGetItem, T_co], None] | None
        self._fdel = None  # type: Callable[[SupportsGetItem], None] | None

        # Process constant value.
        if self.constant:
            self._default = self.process_value(self._default)

        # Increment count.
        _attribute_count += 1
        self._count = _attribute_count

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    @overload
    def __get__(self, instance, owner):
        # type: (SA, None, None) -> SA
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (SA, None, Type[SupportsGetItem]) -> SA | T_co
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (SupportsGetItem, Type[SupportsGetItem]) -> T_co
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
            return instance[self.name]

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
            if self.updatable is None:
                self._updatable = self.fset is not None
            if self.deletable is None:
                self._deletable = self.fdel is not None
            if self.init is None:
                self._init = self.updatable and all((d.has_default or d.delegated) for d in self.recursive_dependencies)
        else:
            if self.updatable is None:
                self._updatable = True
            if self.deletable is None:
                self._deletable = False
            if self.init is None:
                self._init = True
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

    def to_items(self, usecase=None):
        # type: (ItemUsecase | None) -> list[tuple[str, Any]]
        items = [
            ("default", self.default),
            ("factory", self.factory),
            ("required", self.required),
            ("init", self.init),
            ("updatable", self.updatable),
            ("deletable", self.deletable),
            ("constant", self.constant),
            ("repr", self.repr),
            ("eq", self.eq),
            ("order", self.order),
            ("hash", self.hash),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        ]
        if usecase is not ItemUsecase.INIT:
            items.extend(
                [
                    ("name", self.name),
                    ("owner", self.owner),
                    ("delegated", self.delegated),
                    ("count", self.count),
                ]
            )
            if usecase is not ItemUsecase.REPR:
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

    def get_default_value(self):
        # type: () -> T_co
        if self.default is not MISSING:
            default_value = self.default
        elif self.factory is not MISSING:
            default_value = fabricate_value(
                self.factory,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            error = "no valid default/factory"
            raise RuntimeError(error)
        return default_value

    def process_value(self, value):
        # type: (Any) -> T_co
        if self.relationship is not None:
            try:
                return self.relationship.process_value(value)
            except Exception as e:
                exc = type(e)("{!r} attribute; {}".format(self.name, e))
                six.raise_from(exc, None)
                raise exc
        return value

    @overload
    def getter(self, maybe_func):
        # type: (SA, Callable[[SupportsGetItem], T_co]) -> SA
        pass

    @overload
    def getter(self, *dependencies):
        # type: (SA, *StructureAttribute) -> Callable[[Callable[[SupportsGetItem], T_co]], SA]
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
        if self.constant:
            error_ = "can't delegate a constant attribute"
            raise RuntimeError(error_)

        def getter_decorator(func):
            if self.owned:
                error = "attribute {!r} already named and owned by a class".format(self.name)
                raise ValueError(error)
            if self.fget is not None:
                error = "getter delegate already defined"
                raise ValueError(error)
            assert not self._dependencies

            self._dependencies = ()
            for dependency in unique_iterator(dependencies):
                if dependency.owned:
                    error = "dependency attribute {!r} already named and owned by a class".format(dependency.name)
                    raise ValueError(error)
                dependency._dependents += (self,)  # noqa
                self._dependencies += (dependency,)

            self._fget = func
            return self

        if len(dependencies) == 1 and not isinstance(dependencies[0], StructureAttribute) and callable(dependencies[0]):
            return getter_decorator(dependencies[0])
        else:
            return getter_decorator

    @overload
    def setter(self, maybe_func=None):
        # type: (SA, None) -> Callable[[Callable[[SupportsGetItem, T_co], None]], SA]
        pass

    @overload
    def setter(self, maybe_func):
        # type: (SA, Callable[[SupportsGetItem, T_co], None]) -> SA
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
        if self.constant:
            error_ = "can't delegate a constant attribute"
            raise RuntimeError(error_)

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
        # type: (SA, None) -> Callable[[Callable[[SupportsGetItem], None]], SA]
        pass

    @overload
    def deleter(self, maybe_func):
        # type: (SA, Callable[[SupportsGetItem], None]) -> SA
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
        if self.constant:
            error_ = "can't delegate a constant attribute"
            raise RuntimeError(error_)

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

    @overload
    def update(self, __m, **kwargs):
        # type: (SA, SupportsKeysAndGetItem[str, Any], **Any) -> SA
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (SA, Iterable[tuple[str, Any]], **Any) -> SA
        pass

    @overload
    def update(self, **kwargs):
        # type: (SA, **Any) -> SA
        pass

    def update(self, *args, **kwargs):
        init_args = self.to_dict(ItemUsecase.INIT)
        init_args.update(*args, **kwargs)
        return cast(SA, type(self)(**init_args))

    @property
    def name(self):
        # type: () -> str | None
        return self._name

    @property
    def owner(self):
        # type: () -> Type[SupportsGetItem] | None
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
    def relationship(self):
        # type: () -> RT | None
        return self._relationship

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
    def constant(self):
        # type: () -> bool
        return self._constant

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
    def dependencies(self):
        # type: () -> tuple[StructureAttribute, ...]
        return self._dependencies

    @property
    def recursive_dependencies(self):
        # type: () -> tuple[StructureAttribute, ...]
        if self._recursive_dependencies is not None:
            return self._recursive_dependencies
        recursive_dependencies = _traverse(self, direction="dependencies")

        # Cache only if already owned.
        if self.owned:
            self._recursive_dependencies = recursive_dependencies

        return recursive_dependencies

    @property
    def dependents(self):
        # type: () -> tuple[StructureAttribute, ...]
        return self._dependents

    @property
    def recursive_dependents(self):
        # type: () -> tuple[StructureAttribute, ...]
        if self._recursive_dependents is not None:
            return self._recursive_dependents
        recursive_dependents = _traverse(self, direction="dependents")

        # Cache only if already owned.
        if self.owned:
            self._recursive_dependents = recursive_dependents

        return recursive_dependents

    @property
    def fget(self):
        # type: () -> Callable[[SupportsGetItem], T_co] | None
        return self._fget

    @property
    def fset(self):
        # type: () -> Callable[[SupportsGetItem, T_co], None] | None
        return self._fset

    @property
    def fdel(self):
        # type: () -> Callable[[SupportsGetItem], None] | None
        return self._fdel

    @property
    def count(self):
        # type: () -> int
        return self._count

    @property
    def owned(self):
        # type: () -> bool
        owned = self._owner is not None
        assert owned is (self._name is not None)
        return owned

    @property
    def named(self):
        # type: () -> bool
        named = self._name is not None
        assert named is (self._owner is not None)
        return named

    @property
    def delegated(self):
        # type: () -> bool
        return any(d is not None for d in (self.fget, self.fset, self.fdel))

    @property
    def has_default(self):
        # type: () -> bool
        return self.default is not MISSING or self.factory is not MISSING


SA = TypeVar("SA", bound=StructureAttribute)  # base attribute self type


class MutableStructureAttribute(StructureAttribute[T, RT]):
    __slots__ = ()

    def __set__(self, instance, value):
        # type: (SupportsGetSetDeleteItem, T) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        if self.constant:
            error = "can't change constant class attribute {!r}".format(self.name)
            raise AttributeError(error)
        instance[self.name] = value

    def __delete__(self, instance):
        # type: (SupportsGetSetDeleteItem) -> None
        if self.name is None:
            assert self.owner is None
            error = "attribute not named/owned"
            raise RuntimeError(error)
        if self.constant:
            error = "can't delete constant class attribute {!r}".format(self.name)
            raise AttributeError(error)
        del instance[self.name]


def _traverse(attribute, direction):
    # type: (StructureAttribute, Literal["dependencies", "dependents"]) -> tuple[StructureAttribute, ...]
    unvisited = set(getattr(attribute, direction))  # type: set[StructureAttribute]
    visited = set()  # type: set[StructureAttribute]
    while unvisited:
        dep = unvisited.pop()
        if dep in visited:
            continue
        visited.add(dep)
        for sub_dep in getattr(dep, direction):
            unvisited.add(sub_dep)
    return tuple(sorted(visited, key=lambda d: d.count))
