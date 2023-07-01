import six
from basicco import SlottedBaseMeta
from basicco.descriptors import Descriptor, OwnerMeta, Owner, get_descriptors
from basicco.mapping_proxy import MappingProxyType
from tippo import (
    Any,
    Callable,
    Tuple,
    TypeVar,
    Generic,
    Union,
    Type,
    Iterable,
    cast,
    overload,
)

from ._base import Structure, ImmutableStructure, MutableStructure

__all__ = [
    "Attribute",
    "ImmutableAttribute",
    "MutableAttribute",
    "AttributeStructureMeta",
    "AttributeStructure",
    "ImmutableAttributeStructure",
    "MutableAttributeStructure",
]


T = TypeVar("T")


class Attribute(Descriptor, Generic[T]):
    __slots__ = (
        "_constant",
        "_settable",
        "_deletable",
        "_dependencies",
        "_dependents",
        "_fget",
        "_fset",
        "_fdel",
    )

    def __init__(
        self,
        settable=None,  # type: bool | None
        deletable=None,  # type: bool | None
        constant=False,  # type: bool
    ):
        # type: (...) -> None
        super(Attribute, self).__init__()

        if constant:
            if settable is None:
                settable = False
            elif settable:
                raise ValueError("constant attribute can't be settable")

            if deletable is None:
                deletable = False
            elif deletable:
                raise ValueError("constant attribute can't be deletable")

        self._constant = bool(constant)
        self._settable = bool(settable) if settable is not None else None
        self._deletable = bool(deletable) if deletable is not None else None

        self._dependencies = ()  # type: Tuple[Attribute[Any], ...]
        self._dependents = ()  # type: Tuple[Attribute[Any], ...]
        self._fget = None  # type: Union[Callable[[A], T], None]
        self._fset = None  # type: Union[Callable[[A, T], None], None]
        self._fdel = None  # type: Union[Callable[[A], None], None]

    @overload
    def getter(self, *maybe_func):
        # type: (A, Callable[[A], T]) -> A
        pass

    @overload
    def getter(self, *dependencies):
        # type: (A, *Attribute[Any]) -> Callable[[Callable[[A], T]], A]
        pass

    def getter(self, *dependencies):
        # type: (A, *Any) -> Any
        """
        Define a getter method by using a decorator.

        :param dependencies: Attribute dependencies.
        :return: Getter method decorator.
        :raises RuntimeError: Can't define a getter for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Getter already defined.
        """
        if self.constant:
            error_ = "can't define a getter for a constant attribute"
            raise RuntimeError(error_)

        def getter_decorator(func):
            # type: (Callable[[A], T]) -> A
            """Getter decorator."""
            if self.owner is not None:
                error = "{!r} owned by a class".format(self.name)
                raise ValueError(error)
            if self.fget is not None:
                error = "getter already defined"
                raise ValueError(error)
            assert not self._dependencies

            self._dependencies = ()
            for dependency in dependencies:
                assert isinstance(dependency, Attribute)
                if dependency.owner is not None:
                    error = "dependency {!r} owned by a class".format(dependency.name)
                    raise ValueError(error)
                dependency._dependents += (self,)
                self._dependencies += (dependency,)

            self._fget = func
            return self

        if (
            len(dependencies) == 1
            and not isinstance(dependencies[0], Attribute)
            and callable(dependencies[0])
        ):
            return getter_decorator(dependencies[0])
        else:
            return getter_decorator

    @overload
    def setter(self, maybe_func):
        # type: (A, Callable[[A, T], None]) -> A
        pass

    @overload
    def setter(self, maybe_func=None):
        # type: (A, None) -> Callable[[Callable[[A, T], None]], A]
        pass

    def setter(self, maybe_func=None):
        # type: (A, Any) -> Any
        """
        Define a setter method by using a decorator.

        :return: Setter method decorator.
        :raises RuntimeError: Can't define a setter for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not settable.
        :raises ValueError: Need to define a getter before defining a setter.
        :raises ValueError: Setter already defined.
        """
        if self.constant:
            error_ = "can't define a setter for a constant attribute"
            raise RuntimeError(error_)

        def setter_decorator(func):
            # type: (Callable[[A, T], None]) -> A
            """Setter decorator."""
            if self.owner is not None:
                error = "attribute {!r} already named and owned by a class".format(
                    self.name
                )
                raise ValueError(error)
            if self.settable is False:
                error = "attribute is not settable, can't define setter"
                raise ValueError(error)
            if self.fget is None:
                error = "need to define a getter before defining a setter"
                raise ValueError(error)
            if self.fset is not None:
                error = "setter already defined"
                raise ValueError(error)
            self._fset = func
            return self

        if maybe_func is not None:
            return setter_decorator(maybe_func)
        else:
            return setter_decorator

    @overload
    def deleter(self, maybe_func=None):
        # type: (A, None) -> Callable[[Callable[[AttributeStructure], None]], A]
        pass

    @overload
    def deleter(self, maybe_func):
        # type: (A, Callable[[AttributeStructure], None]) -> A
        pass

    def deleter(self, maybe_func=None):
        # type: (A, Any) -> Any
        """
        Define a deleter method by using a decorator.

        :return: Deleter method decorator.
        :raises RuntimeError: Can't define a deleter for a constant attribute.
        :raises ValueError: Attribute already named and owned by a class.
        :raises ValueError: Attribute is not deletable.
        :raises ValueError: Need to define a getter before defining a deleter.
        :raises ValueError: Deleter already defined.
        """
        if self.constant:
            error_ = "can't define a deleter for a constant attribute"
            raise RuntimeError(error_)

        def deleter_decorator(func):
            # type: (Callable[[A], None]) -> A
            """Deleter decorator."""
            if self.owner is not None:
                error = "attribute {!r} already named and owned by a class".format(
                    self.name
                )
                raise ValueError(error)
            if self.deletable is False:
                error = "attribute is not deletable, can't define deleter"
                raise ValueError(error)
            if self.fget is None:
                error = "need to define a getter before defining a deleter"
                raise ValueError(error)
            if self.fdel is not None:
                error = "deleter already defined"
                raise ValueError(error)
            self._fdel = func
            return self

        if maybe_func is not None:
            return deleter_decorator(maybe_func)
        else:
            return deleter_decorator

    @property
    def settable(self):
        # type: () -> Union[bool, None]
        return self._settable

    @property
    def deletable(self):
        # type: () -> Union[bool, None]
        return self._deletable

    @property
    def constant(self):
        # type: () -> bool
        return self._constant

    @property
    def dependencies(self):
        # type: () -> Tuple[Attribute[Any], ...]
        return self._dependencies

    @property
    def dependents(self):
        # type: () -> Tuple[Attribute[Any], ...]
        return self._dependents

    @property
    def fget(self):
        # type: () -> Union[Callable[[A], T], None]
        return self._fget

    @property
    def fset(self):
        # type: () -> Union[Callable[[A, T], None], None]
        return self._fset

    @property
    def fdel(self):
        # type: () -> Union[Callable[[A], None], None]
        return self._fdel


A = TypeVar("A", bound=Attribute[Any])


class ImmutableAttribute(Attribute[T]):
    __slots__ = ()


class MutableAttribute(Attribute[T]):
    __slots__ = ()


class AttributeStructureMeta(OwnerMeta, SlottedBaseMeta):
    pass


class AttributeStructure(six.with_metaclass(AttributeStructureMeta, Owner, Structure)):
    __slots__ = ()


AS = TypeVar("AS", bound=AttributeStructure)


class ImmutableAttributeStructure(ImmutableStructure, AttributeStructure):
    __slots__ = ()


class MutableAttributeStructure(MutableStructure, AttributeStructure):
    __slots__ = ()


def get_attributes(
    cls,  # type: Union[Type[AttributeStructure], AttributeStructureMeta]
    base_cls=None,  # type: Union[Type[A], Iterable[Type[A]], None]
    inherited=True,  # type: bool
):
    # type: (...) -> MappingProxyType[str, A]
    """
    Get descriptors in owner class.

    :param cls: Descriptor owner class.
    :param base_cls: Base descriptor class(es).
    :param inherited: Whether to include parent classes' descriptors.
    :return: Ordered descriptors mapped by name.
    """
    if base_cls is None:
        base_cls = cast("Type[A]", Attribute)
    return get_descriptors(cls, base_cls=base_cls, inherited=inherited)
