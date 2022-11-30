"""Helper functions."""

import six
from basicco import caller_module, custom_repr, dynamic_class, fabricate_value
from basicco.namespace import Namespace
from tippo import Any, Callable, Iterable, Mapping, Type, TypeVar, cast

from ._attribute import Attribute
from ._dict import DictStructure
from ._list import ListStructure
from ._relationship import Relationship
from ._set import SetStructure
from .constants import MISSING, MissingType
from .serializers import Serializer, TypedSerializer

T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


def dict_cls(
    converter=None,  # type: Callable[[Any], VT] | Type[VT] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[VT] | str | None] | Type[VT] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[VT] | None
    key_converter=None,  # type: Callable[[Any], KT] | Type[KT] | str | None
    key_validator=None,  # type: Callable[[Any], None] | str | None
    key_types=(),  # type: Iterable[Type[KT] | str | None] | Type[KT] | str | None
    key_subtypes=False,  # type: bool
    key_serializer=TypedSerializer(),  # type: Serializer[KT] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    qualified_name=None,  # type: str | None
    dict_type=DictStructure,  # type: Type[DictStructure[KT, VT]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[VT]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
    key_relationship_type=Relationship,  # type: Type[Relationship[KT]]
    key_relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> Type[DictStructure[KT, VT]]
    """
    Build a dictionary structure class.

    :param converter: Callable value converter.
    :param validator: Callable value validator.
    :param types: Types for runtime value checking.
    :param subtypes: Whether to accept subtypes for values.
    :param serializer: Value serializer.
    :param key_converter: Callable key converter.
    :param key_validator: Callable key validator.
    :param key_types: Types for runtime key checking.
    :param key_subtypes: Whether to accept subtypes for keys.
    :param key_serializer: Key serializer.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    :param qualified_name: Qualified name.
    :param dict_type: Base class.
    :param cls_dct: Class body.
    :param cls_module: Class module.
    :param relationship_type: Value relationship class.
    :param relationship_kwargs: Value relationship keyword arguments.
    :param key_relationship_type: Key relationship class.
    :param key_relationship_kwargs: Key relationship keyword arguments.
    :return: Dictionary structure class.
    """

    # Caller module.
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    # Relationships.
    relationship = relationship_type(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        **(relationship_kwargs or {}),  # noqa
    )
    key_relationship = key_relationship_type(
        converter=key_converter,
        validator=key_validator,
        types=key_types,
        subtypes=key_subtypes,
        serializer=key_serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        **(key_relationship_kwargs or {}),  # noqa
    )

    # Class body.
    cls_dct = dict(cls_dct or {})
    cls_dct["relationship"] = relationship
    cls_dct["key_relationship"] = key_relationship

    # Build class and return it.
    return cast(
        Type[DictStructure[KT, VT]],
        dynamic_class.make_cls(
            qualified_name or dict_type.__qualname__,
            bases=(dict_type,),
            dct=cls_dct,
            module=cls_module,
        ),
    )


def list_cls(
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    qualified_name=None,  # type: str | None
    list_type=ListStructure,  # type: Type[ListStructure[T]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[T]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> Type[ListStructure[T]]
    """
    Build a list structure class.

    :param converter: Callable value converter.
    :param validator: Callable value validator.
    :param types: Types for runtime checking.
    :param subtypes: Whether to accept subtypes.
    :param serializer: Serializer.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    :param qualified_name: Qualified name.
    :param list_type: Base class.
    :param cls_dct: Class body.
    :param cls_module: Class module.
    :param relationship_type: Relationship class.
    :param relationship_kwargs: Relationship keyword arguments.
    :return: List structure class.
    """

    # Caller module.
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    # Relationship.
    relationship = relationship_type(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        **(relationship_kwargs or {}),  # noqa
    )

    # Class body.
    cls_dct = dict(cls_dct or {})
    cls_dct["relationship"] = relationship

    # Build class and return it.
    return cast(
        Type[ListStructure[T]],
        dynamic_class.make_cls(
            qualified_name or list_type.__qualname__,
            bases=(list_type,),
            dct=cls_dct,
            module=cls_module,
        ),
    )


def set_cls(
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    qualified_name=None,  # type: str | None
    set_type=SetStructure,  # type: Type[SetStructure[T]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[T]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> Type[SetStructure[T]]
    """
    Build a set structure class.

    :param converter: Callable value converter.
    :param validator: Callable value validator.
    :param types: Types for runtime checking.
    :param subtypes: Whether to accept subtypes.
    :param serializer: Serializer.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    :param qualified_name: Qualified name.
    :param set_type: Base class.
    :param cls_dct: Class body.
    :param cls_module: Class module.
    :param relationship_type: Relationship class.
    :param relationship_kwargs: Relationship keyword arguments.
    :return: Set structure class.
    """

    # Caller module.
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    # Relationship.
    relationship = relationship_type(
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        **(relationship_kwargs or {}),  # noqa
    )

    # Class body.
    cls_dct = dict(cls_dct or {})
    cls_dct["relationship"] = relationship

    # Build class and return it.
    return cast(
        Type[SetStructure[T]],
        dynamic_class.make_cls(
            qualified_name or set_type.__qualname__,
            bases=(set_type,),
            dct=cls_dct,
            module=cls_module,
        ),
    )


def attribute(
    default=MISSING,  # type: T | MissingType
    factory=MISSING,  # type: Callable[..., T] | str | MissingType
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    init_as=None,  # type: T | str | None
    settable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    serializable=None,  # type: bool | None
    serialize_as=None,  # type: T | str | None
    serialize_default=True,  # type: bool
    constant=False,  # type: bool
    repr=None,  # type: bool | Callable[[T], str] | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    doc="",  # type: str
    metadata=None,  # type: Any
    namespace=None,  # type: Namespace | Mapping[str, Any] | None
    callback=None,  # type: Callable[[Attribute[T]], None] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    attribute_type=Attribute,  # type: Type[Attribute[T]]
    attribute_kwargs=None,  # type: Mapping[str, Any] | None
    relationship_type=Relationship,  # type: Type[Relationship[T]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> T
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
    :param init_as: Alternative attribute or name to use when initializing.
    :param settable: Whether the value can be changed after being set.
    :param deletable: Whether the value can be deleted.
    :param serializable: Whether it's serializable.
    :param serialize_as: Alternative attribute or name to use when serializing.
    :param serialize_default: Whether to serialize default value.
    :param constant: Whether attribute is a class constant.
    :param repr: Whether to include in the `__repr__` method.
    :param eq: Whether to include in the `__eq__` method.
    :param order: Whether to include in the `__lt__`, `__le__`, `__gt__`, `__ge__` methods.
    :param hash: Whether to include in the `__hash__` method.
    :param doc: Documentation.
    :param metadata: User metadata.
    :param namespace: Namespace.
    :param callback: Callback that runs after attribute has been named/owned by class.
    :param extra_paths: Extra module paths in fallback order.
    :param builtin_paths: Builtin module paths in fallback order.
    :param attribute_type: Attribute class.
    :param attribute_kwargs: Attribute keyword arguments.
    :param relationship_type: Relationship class.
    :param relationship_kwargs: Relationship keyword arguments.
    :return: Attribute.
    """

    # Caller module.
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))

    # Build attribute and return it.
    return cast(
        T,
        attribute_type(
            default=default,
            factory=factory,
            relationship=relationship_type(
                converter=converter,
                validator=validator,
                types=types,
                subtypes=subtypes,
                serializer=serializer,
                extra_paths=extra_paths,
                builtin_paths=builtin_paths,
                **(relationship_kwargs or {}),  # noqa
            ),
            required=required,
            init=init,
            init_as=init_as,  # type: ignore
            settable=settable,
            deletable=deletable,
            serializable=serializable,
            serialize_as=serialize_as,  # type: ignore
            serialize_default=serialize_default,
            constant=constant,
            repr=repr,
            eq=eq,
            order=order,
            hash=hash,
            doc=doc,
            metadata=metadata,
            namespace=namespace,
            callback=callback,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
            **(attribute_kwargs or {}),  # noqa
        ),
    )


def dict_attribute(
    default=MISSING,  # type: Mapping[KT, VT] | MissingType
    factory=MISSING,  # type: Callable[..., Mapping[KT, VT]] | str | MissingType
    converter=None,  # type: Callable[[Any], VT] | Type[VT] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[VT] | str | None] | Type[VT] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[VT] | None
    key_converter=None,  # type: Callable[[Any], KT] | Type[KT] | str | None
    key_validator=None,  # type: Callable[[Any], None] | str | None
    key_types=(),  # type: Iterable[Type[KT] | str | None] | Type[KT] | str | None
    key_subtypes=False,  # type: bool
    key_serializer=TypedSerializer(),  # type: Serializer[KT] | None
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    init_as=None,  # type: Mapping[KT, VT] | str | None
    settable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    serializable=None,  # type: bool | None
    serialize_as=None,  # type: Mapping[KT, VT] | str | None
    serialize_default=True,  # type: bool
    constant=False,  # type: bool
    repr=None,  # type: bool | Callable[[DictStructure[KT, VT]], str] | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    doc="",  # type: str
    metadata=None,  # type: Any
    callback=None,  # type: Callable[[Attribute[DictStructure[KT, VT]]], None] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    attribute_type=Attribute,  # type: Type[Attribute[DictStructure[KT, VT]]]
    attribute_kwargs=None,  # type: Mapping[str, Any] | None
    dict_type=DictStructure,  # type: Type[DictStructure[KT, VT]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[VT]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
    key_relationship_type=Relationship,  # type: Type[Relationship[KT]]
    key_relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> DictStructure[KT, VT]
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    if not constant and repr is None:
        repr = custom_repr.mapping_repr

    cls = dict_cls(
        qualified_name=dict_type.__name__,
        cls_module=cls_module,
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        key_converter=key_converter,
        key_validator=key_validator,
        key_types=key_types,
        key_subtypes=key_subtypes,
        key_serializer=key_serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        dict_type=dict_type,
        cls_dct=cls_dct,
        relationship_type=relationship_type,
        key_relationship_type=key_relationship_type,
        relationship_kwargs=relationship_kwargs,
        key_relationship_kwargs=key_relationship_kwargs,
    )  # type: Type[DictStructure[KT, VT]]

    _namespace = {}  # type: dict[str, Any]

    def _callback(attr, _ns=_namespace, _cls=cls, _cb=callback):  # noqa
        _ns[_cls.__name__] = _cls
        _cls.__qualname__ = "{}.__attrs__.{}.namespace.{}".format(attr.owner.__qualname__, attr.name, _cls.__name__)
        if _cb is not None:
            _cb(attr)

    def _converter(value, _cls=cls, _conv=converter, _kconv=key_converter):
        if _conv is not None or _kconv is not None:
            value = dict(
                (fabricate_value.fabricate_value(_kconv, k), fabricate_value.fabricate_value(_conv, v))
                for k, v in six.iteritems(value)
            )
        return _cls(value)

    return cast(
        DictStructure[KT, VT],
        attribute(
            default=default,
            factory=factory,
            converter=_converter,
            validator=validator,
            types=(cls,),
            subtypes=False,
            serializer=serializer,
            required=required,
            init=init,
            init_as=init_as,  # type: ignore
            settable=settable,
            deletable=deletable,
            serializable=serializable,
            serialize_as=serialize_as,  # type: ignore
            serialize_default=serialize_default,
            constant=constant,
            repr=repr,
            eq=eq,
            order=order,
            hash=hash,
            doc=doc,
            metadata=metadata,
            namespace=_namespace,
            callback=_callback,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
            attribute_type=attribute_type,
            relationship_type=relationship_type,
            attribute_kwargs=attribute_kwargs,
            relationship_kwargs=relationship_kwargs,
        ),
    )


def list_attribute(
    default=MISSING,  # type: Iterable[T] | MissingType
    factory=MISSING,  # type: Callable[..., Iterable[T]] | str | MissingType
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    init_as=None,  # type: Iterable[T] | str | None
    settable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    serializable=None,  # type: bool | None
    serialize_as=None,  # type: Iterable[T] | str | None
    serialize_default=True,  # type: bool
    constant=False,  # type: bool
    repr=None,  # type: bool | Callable[[ListStructure[T]], str] | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    doc="",  # type: str
    metadata=None,  # type: Any
    callback=None,  # type: Callable[[Attribute[ListStructure[T]]], None] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    attribute_type=Attribute,  # type: Type[Attribute[ListStructure[T]]]
    attribute_kwargs=None,  # type: Mapping[str, Any] | None
    list_type=ListStructure,  # type: Type[ListStructure[T]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[T]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> ListStructure[T]
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    if not constant and repr is None:
        repr = custom_repr.iterable_repr

    cls = list_cls(
        qualified_name=list_type.__name__,
        cls_module=cls_module,
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        list_type=list_type,
        cls_dct=cls_dct,
        relationship_type=relationship_type,
        relationship_kwargs=relationship_kwargs,
    )  # type: Type[ListStructure[T]]

    _namespace = {}  # type: dict[str, Any]

    def _callback(attr, _ns=_namespace, _cls=cls, _cb=callback):  # noqa
        _ns[_cls.__name__] = _cls
        _cls.__qualname__ = "{}.__attrs__.{}.namespace.{}".format(attr.owner.__qualname__, attr.name, _cls.__name__)
        if _cb is not None:
            _cb(attr)

    def _converter(value, _cls=cls, _conv=converter):
        if _conv is not None:
            value = [fabricate_value.fabricate_value(_conv, v) for v in value]
        return _cls(value)

    return cast(
        ListStructure[T],
        attribute(
            default=default,
            factory=factory,
            converter=_converter,
            validator=validator,
            types=(cls,),
            subtypes=False,
            serializer=serializer,
            required=required,
            init=init,
            init_as=init_as,  # type: ignore
            settable=settable,
            deletable=deletable,
            serializable=serializable,
            serialize_as=serialize_as,  # type: ignore
            serialize_default=serialize_default,
            constant=constant,
            repr=repr,
            eq=eq,
            order=order,
            hash=hash,
            doc=doc,
            metadata=metadata,
            namespace=_namespace,
            callback=_callback,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
            attribute_type=attribute_type,
            relationship_type=relationship_type,
            attribute_kwargs=attribute_kwargs,
            relationship_kwargs=relationship_kwargs,
        ),
    )


def set_attribute(
    default=MISSING,  # type: Iterable[T] | MissingType
    factory=MISSING,  # type: Callable[..., Iterable[T]] | str | MissingType
    converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
    validator=None,  # type: Callable[[Any], None] | str | None
    types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
    subtypes=False,  # type: bool
    serializer=TypedSerializer(),  # type: Serializer[T] | None
    required=None,  # type: bool | None
    init=None,  # type: bool | None
    init_as=None,  # type: Iterable[T] | str | None
    settable=None,  # type: bool | None
    deletable=None,  # type: bool | None
    serializable=None,  # type: bool | None
    serialize_as=None,  # type: Iterable[T] | str | None
    serialize_default=True,  # type: bool
    constant=False,  # type: bool
    repr=None,  # type: bool | Callable[[SetStructure[T]], str] | None
    eq=None,  # type: bool | None
    order=None,  # type: bool | None
    hash=None,  # type: bool | None
    doc="",  # type: str
    metadata=None,  # type: Any
    callback=None,  # type: Callable[[Attribute[SetStructure[T]]], None] | None
    extra_paths=(),  # type: Iterable[str]
    builtin_paths=None,  # type: Iterable[str] | None
    attribute_type=Attribute,  # type: Type[Attribute[SetStructure[T]]]
    attribute_kwargs=None,  # type: Mapping[str, Any] | None
    set_type=SetStructure,  # type: Type[SetStructure[T]]
    cls_dct=None,  # type: Mapping[str, Any] | None
    cls_module=None,  # type: str | None
    relationship_type=Relationship,  # type: Type[Relationship[T]]
    relationship_kwargs=None,  # type: Mapping[str, Any] | None
):
    # type: (...) -> SetStructure[T]
    caller_mod = caller_module.caller_module()
    extra_paths = tuple(tuple(extra_paths) or (m for m in (caller_mod,) if m))
    if cls_module is None:
        cls_module = caller_mod

    if not constant and repr is None:
        repr = lambda s: custom_repr.iterable_repr(s, prefix="{", suffix="}")

    cls = set_cls(
        qualified_name=set_type.__name__,
        cls_module=cls_module,
        converter=converter,
        validator=validator,
        types=types,
        subtypes=subtypes,
        serializer=serializer,
        extra_paths=extra_paths,
        builtin_paths=builtin_paths,
        set_type=set_type,
        cls_dct=cls_dct,
        relationship_type=relationship_type,
        relationship_kwargs=relationship_kwargs,
    )  # type: Type[SetStructure[T]]

    _namespace = {}  # type: dict[str, Any]

    def _callback(attr, _ns=_namespace, _cls=cls, _cb=callback):  # noqa
        _ns[_cls.__name__] = _cls
        _cls.__qualname__ = "{}.__attrs__.{}.namespace.{}".format(attr.owner.__qualname__, attr.name, _cls.__name__)
        if _cb is not None:
            _cb(attr)

    def _converter(value, _cls=cls, _conv=converter):
        if _conv is not None:
            value = [fabricate_value.fabricate_value(_conv, v) for v in value]
        return _cls(value)

    return cast(
        SetStructure[T],
        attribute(
            default=default,
            factory=factory,
            converter=_converter,
            validator=validator,
            types=(cls,),
            subtypes=False,
            serializer=serializer,
            required=required,
            init=init,
            init_as=init_as,  # type: ignore
            settable=settable,
            deletable=deletable,
            serializable=serializable,
            serialize_as=serialize_as,  # type: ignore
            serialize_default=serialize_default,
            constant=constant,
            repr=repr,
            eq=eq,
            order=order,
            hash=hash,
            doc=doc,
            metadata=metadata,
            namespace=_namespace,
            callback=_callback,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
            attribute_type=attribute_type,
            relationship_type=relationship_type,
            attribute_kwargs=attribute_kwargs,
            relationship_kwargs=relationship_kwargs,
        ),
    )
