from tippo import Any, Callable, TypeVar, Type, Iterable, cast
from basicco import caller_module
from estruttura import MissingType, MISSING

from ._attribute import DataAttribute
from ._relationship import DataRelationship


T_co = TypeVar("T_co", covariant=True)


def attribute(
    default=MISSING,  # type: Any
    factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    updatable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    constant=False,  # type: bool
    repr=None,  # type: bool | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    serialized=None,  # type: bool | None
    metadata=None,  # type: Any
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    converter=None,  # type: Callable[[Any], T_co] | Type[T_co] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T_co] | Type | str | None] | Type[T_co] | Type | str | None
    subtypes=False,  # type: bool
    serializer=MISSING,  # type: Callable[[T_co], Any] | str | None | MissingType
    deserializer=MISSING,  # type: Callable[[Any], T_co] | str | None | MissingType
):
    # type: (...) -> T_co
    module = caller_module.caller_module()
    if module is not None:
        extra_paths = (module,) + tuple(extra_paths)

    relationship = DataRelationship(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        deserializer=deserializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
    )

    attribute_ = DataAttribute(
        default=default,
        factory=factory,
        required=required,
        init=init,
        updatable=updatable,
        deletable=deletable,
        constant=constant,
        repr=repr,
        eq=eq,
        order=order,
        hash=hash,
        serialized=serialized,
        relationship=relationship,
        metadata=metadata,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
    )  # type: DataAttribute[T_co]

    return cast(T_co, attribute_)


def relationship(
    converter=None,  # type: Callable[[Any], T_co] | Type[T_co] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T_co] | Type | str | None] | Type[T_co] | Type | str | None
    subtypes=False,  # type: bool
    serializer=MISSING,  # type: Callable[[T_co], Any] | str | None | MissingType
    deserializer=MISSING,  # type: Callable[[Any], T_co] | str | None | MissingType
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
):
    # type: (...) -> DataRelationship[T_co]
    module = caller_module.caller_module()
    if module is not None:
        extra_paths = (module,) + tuple(extra_paths)

    return DataRelationship(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        deserializer=deserializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
    )
