"""Factory functions to make objects."""

from basicco import caller_module
from tippo import Any, Callable, Iterable, Type, TypeVar, cast

from ._attribute import Attribute
from ._relationship import Relationship, Serializer, TypedSerializer
from .constants import MISSING, MissingType

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


def relationship(
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
):
    # type: (...) -> Relationship[T]
    """
    Define a relationship.

    :param converter: Callable value converter.
    :param validator: Callable value validator.
    :param types: Types for runtime checking.
    :param subtypes: Whether to accept subtypes.
    :param serializer: Serializer.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    :return: Relationship.
    """
    module = caller_module.caller_module()
    if module:
        extra_paths = (module,) + tuple(extra_paths)
    return Relationship(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
    )


def attribute(
    default=MISSING,  # type: T_co | MissingType
    factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    settable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    serializable=None,  # type: bool | None
    serialize_as=None,  # type: str | None
    serialize_default=True,  # type: bool
    constant=False,  # type: bool
    repr=None,  # type: bool | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    doc="",  # type: str
    metadata=None,  # type: Any
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
):
    # type: (...) -> T_co
    """
    Define an attribute.

    :param default: Default value.
    :param factory: Default factory.
    :param converter: Callable value converter.
    :param validator: Callable value validator.
    :param types: Types for runtime checking.
    :param subtypes: Whether to accept subtypes.
    :param serializer: Serializer.
    :param required: Whether it is required to have a value.
    :param init: Whether to include in the `__init__` method.
    :param settable: Whether the value can be changed after being set.
    :param deletable: Whether the value can be deleted.
    :param serializable: Whether it's serializable.
    :param serialize_as: Name to use when serializing.
    :param serialize_default: Whether to serialize default value.
    :param constant: Whether attribute is a class constant.
    :param repr: Whether to include in the `__repr__` method.
    :param eq: Whether to include in the `__eq__` method.
    :param order: Whether to include in the `__lt__`, `__le__`, `__gt__`, `__ge__` methods.
    :param hash: Whether to include in the `__hash__` method.
    :param doc: Documentation.
    :param metadata: User metadata.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    """
    module = caller_module.caller_module()
    if module:
        extra_paths = (module,) + tuple(extra_paths)
    return cast(
        T_co,
        Attribute(
            default=default,
            factory=factory,
            relationship=Relationship(
                converter=converter,
                validator=validator,
                types=types,
                subtypes=subtypes,
                serializer=serializer,
                extra_paths=extra_paths,
                builtin_paths=builtin_paths,
            ),
            required=required,
            init=init,
            settable=settable,
            deletable=deletable,
            serializable=serializable,
            serialize_as=serialize_as,
            serialize_default=serialize_default,
            constant=constant,
            repr=repr,
            eq=eq,
            order=order,
            hash=hash,
            doc=doc,
            metadata=metadata,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        ),
    )


def getter(delegated_attribute, dependencies=()):
    # type: (T, Iterable) -> Callable[[Callable[[Any], T]], None]
    """
    Decorator that sets a getter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param delegated_attribute: Attribute.
    :param dependencies: Dependencies.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any], T]) -> None
        """Getter decorator."""
        if func.__name__ != "_":
            error = "getter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], delegated_attribute).getter(*dependencies)(func)

    return decorator


def setter(delegated_attribute):
    # type: (T) -> Callable[[Callable[[Any, T], None]], None]
    """
    Decorator that sets a setter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param delegated_attribute: Attribute.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any, T], None]) -> None
        """Setter decorator."""
        if func.__name__ != "_":
            error = "setter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], delegated_attribute).setter(func)

    return decorator


def deleter(delegated_attribute):
    # type: (T) -> Callable[[Callable[[Any], None]], None]
    """
    Decorator that sets a deleter delegate for an attribute.
    The decorated function should be named as a single underscore: `_`.

    :param delegated_attribute: Attribute.
    :return: Delegate function decorator.
    """

    def decorator(func):
        # type: (Callable[[Any], None]) -> None
        """Deleter decorator."""
        if func.__name__ != "_":
            error = "deleter function needs to be named '_' instead of {!r}".format(func.__name__)
            raise NameError(error)
        cast(Attribute[T], delegated_attribute).deleter(func)

    return decorator
