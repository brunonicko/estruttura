"""Relationship between objects and values."""

import six
from basicco import SlottedBase, basic_data, fabricate_value, type_checking
from basicco.abstract_class import abstract
from basicco.import_path import get_path, import_path
from tippo import (
    Any,
    Callable,
    Generic,
    Iterable,
    Mapping,
    SupportsKeysAndGetItem,
    Tuple,
    Type,
    TypeVar,
    cast,
    get_origin,
    overload,
)

from .constants import BASIC_TYPES, MISSING
from .exceptions import (
    ConversionError,
    InvalidTypeError,
    ProcessingError,
    SerializationError,
    ValidationError,
)

T = TypeVar("T")


class Serializer(SlottedBase, Generic[T]):
    """Abstract serializer."""

    __slots__ = ()

    @abstract
    def serialize(self, relationship, value):
        # type: (Relationship[T], T) -> Any
        """
        Serialize value.

        :param relationship: Relationship.
        :param value: Value.
        :return: Serialized value.
        :raises SerializationError: Error while serializing.
        """
        raise NotImplementedError()

    @abstract
    def deserialize(self, relationship, serialized):
        # type: (Relationship[T], Any) -> T
        """
        Deserialize value.

        :param relationship: Relationship.
        :param serialized: Serialized value.
        :return: Value.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()


class TypedSerializer(Serializer[T]):
    """Serializer that utilizes relationship types to best guess serialization formatting."""

    __slots__ = (
        "_types",
        "_subtypes",
        "_resolved_types",
        "_basic_types",
        "_complex_types",
        "_extra_paths",
        "_builtin_paths",
    )

    def serialize(self, relationship, value):
        # type: (Relationship[T], T) -> Any
        """
        Serialize value.

        :param relationship: Relationship.
        :param value: Value.
        :return: Serialized value.
        :raises SerializationError: Error while serializing.
        """

        # Value is of basic type, passthrough.
        if isinstance(value, BASIC_TYPES):
            return value

        # Value is a class, serialize as a path with special '__class__' keyword.
        if isinstance(value, type):
            return {
                "__class__": get_path(
                    value,
                    extra_paths=relationship.extra_paths,
                    builtin_paths=relationship.builtin_paths,
                )
            }

        # Value has 'serialize' method.
        serializer = getattr(value, "serialize", None)
        if callable(serializer):
            try:
                serialized = serializer()
            except (TypeError, ValueError) as e:
                raise SerializationError(e)

        # Unsupported non-serializable type.
        else:
            error = "{!r} object does not implement a 'serialize()' method".format(type(value).__name__)
            raise SerializationError(error)

        # Ambiguous types, wrap the serialized value in a dictionary with special '__class__' and '__state__' keywords.
        if relationship.subtypes or (
            len(relationship.types_info.complex_types) > 1
            and not (len(relationship.types_info.mapping_types) == 1 and isinstance(serialized, dict))
            and not (len(relationship.types_info.iterable_types) == 1 and isinstance(serialized, list))
        ):
            serialized = {
                "__class__": get_path(
                    type(value),
                    extra_paths=relationship.extra_paths,
                    builtin_paths=relationship.builtin_paths,
                ),
                "__state__": serialized,
            }

        return serialized

    def deserialize(self, relationship, serialized):
        # type: (Relationship[T], Any) -> T
        """
        Deserialize value.

        :param relationship: Relationship.
        :param serialized: Serialized value.
        :return: Value.
        :raises SerializationError: Error while deserializing.
        """

        # Serialized value is of basic type, passthrough.
        if isinstance(serialized, BASIC_TYPES):
            return cast(T, serialized)

        # Serialized class path in a dictionary, try to import it.
        cls = None
        cls_import_error = None
        if isinstance(serialized, dict) and "__class__" in serialized:
            if all(k.startswith("__") and k.endswith("__") for k in serialized):
                try:
                    cls = import_path(
                        serialized["__class__"],
                        extra_paths=relationship.extra_paths,
                        builtin_paths=relationship.builtin_paths,
                    )
                except (ImportError, ValueError, AttributeError) as e:
                    cls_import_error = e
                else:

                    # Imported class but no state is present, so value is the class itself.
                    if "__state__" not in serialized:
                        return cls

        # Class was imported, get state.
        if cls is not None:
            state = serialized["__state__"]

        # No complex types defined to deserialize.
        elif not relationship.types_info.complex_types:
            error = "not enough types defined to deserialize {!r}".format(serialized)
            raise SerializationError(error)

        # Accepts subtypes or more than one complex type.
        elif relationship.subtypes or len(relationship.types_info.complex_types) > 1:

            # Infer mapping type.
            if (
                not relationship.subtypes
                and len(relationship.types_info.mapping_types) == 1
                and isinstance(serialized, dict)
            ):
                cls = relationship.types_info.mapping_types[0]
                state = serialized

            # Infer iterable type.
            elif (
                not relationship.subtypes
                and len(relationship.types_info.iterable_types) == 1
                and isinstance(serialized, list)
            ):
                cls = relationship.types_info.iterable_types[0]
                state = serialized

            # Too many complex types defined to deserialize.
            else:
                error = "ambiguous types when deserializing {!r}".format(serialized)
                raise SerializationError(error)

        # Single complex type, no subtype.
        else:
            cls = relationship.types_info.complex_types[0]
            state = serialized

        # Use class deserializer method if available.
        deserializer = getattr(cls, "deserialize", None)
        if callable(deserializer):
            try:
                value = deserializer(state)
            except (TypeError, ValueError) as e:

                # If we had a class import error, raise that one instead. It's most likely the real error.
                if cls_import_error is not None:
                    six.raise_from(cls_import_error, None)
                    raise cls_import_error

                raise SerializationError(e)

        else:
            error = "{!r} object does not implement a 'deserialize()' method".format(type(serialized).__name__)
            raise SerializationError(error)

        return value


class Relationship(basic_data.ImmutableBasicData, Generic[T]):
    """Describes a relationship between an object and its values."""

    __slots__ = (
        "_converter",
        "_validator",
        "_types",
        "_subtypes",
        "_serializer",
        "_extra_paths",
        "_builtin_paths",
        "_types_info",
    )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        validator=None,  # type: Callable[[Any], None] | str | None
        types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
        subtypes=False,  # type: bool
        serializer=TypedSerializer(),  # type: Serializer[T] | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param validator: Callable value validator.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param serializer: Serializer.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        self._converter = fabricate_value.format_factory(converter)
        self._validator = fabricate_value.format_factory(validator)
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._serializer = serializer
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None
        self._types_info = None  # type: RelationshipTypesInfo[T] | None

    def convert_value(self, value):
        # type: (Any) -> T
        """
        Convert a value.

        :param value: Value.
        :return: Converted value.
        :raises ConversionError: Conversion failed.
        """
        if self.converter is not None:
            try:
                return fabricate_value.fabricate_value(
                    self.converter,
                    value,
                    extra_paths=self._extra_paths,
                    builtin_paths=self._builtin_paths,
                )
            except (ConversionError, TypeError, ValueError) as e:
                exc = ConversionError(str(e))
                six.raise_from(exc, None)
                raise exc
        return cast(T, value)

    def validate_value(self, value):
        # type: (Any) -> None
        """
        Validate a value.

        :param value: Value.
        :raises ValidationError: Validation failed.
        """
        if self.validator is not None:
            try:
                fabricate_value.fabricate_value(
                    self.validator,
                    value,
                    extra_paths=self._extra_paths,
                    builtin_paths=self._builtin_paths,
                )
            except ValidationError as e:
                exc = ValidationError(str(e))
                six.raise_from(exc, None)
                raise exc

    def check_value_type(self, value):
        # type: (Any) -> None
        """
        Check value type.

        :param value: Value.
        :raises InvalidTypeError: Invalid value type.
        """
        if self.types:
            try:
                type_checking.assert_is_instance(
                    value,
                    self.types,
                    subtypes=self.subtypes,
                    extra_paths=self.extra_paths,
                    builtin_paths=self.builtin_paths,
                )
            except type_checking.TypeCheckError as e:
                exc = InvalidTypeError(str(e))
                six.raise_from(exc, None)
                raise exc

    def process_value(self, value, location=MISSING):
        # type: (Any, Any) -> T
        """
        Process value (convert, check type, validate).

        :param value: Value.
        :param location: Optional value location information.
        :return: Processed value.
        :raises ProcessingError: Error while processing value.
        """
        try:
            converted_value = self.convert_value(value)  # type: T
            self.check_value_type(converted_value)
            self.validate_value(converted_value)
        except ProcessingError as e:
            if location is not MISSING:
                error = "{!r}; {}".format(location, e)
            else:
                error = str(e)
            exc = type(e)(error)
            six.raise_from(exc, None)
            raise exc
        return converted_value

    def accepts_type(self, value):
        # type: (Any) -> bool
        """
        Get whether the type of a value is accepted or not.

        :param value: Value.
        :return: True if type is accepted.
        """
        return type_checking.is_instance(
            value,
            self.types,
            subtypes=self.subtypes,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

    def serialize_value(self, value):
        # type: (T) -> Any
        """
        Serialize value.

        :param value: Value.
        :return: Serialized value.
        :raises SerializationError: Error while serializing.
        """
        if self.serializer is None:
            error = "no serializer defined"
            raise SerializationError(error)
        return self.serializer.serialize(self, value)

    def deserialize_value(self, serialized):
        # type: (Any) -> T
        """
        Deserialize value.

        :param serialized: Serialized value.
        :return: Value.
        :raises SerializationError: Error while deserializing.
        """
        if self.serializer is None:
            error = "no serializer defined"
            raise SerializationError(error)
        return self.serializer.deserialize(self, serialized)

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
        """
        Convert to items.

        :param usecase: Usecase.
        :return: Items.
        """
        return [
            ("converter", self.converter),
            ("validator", self.validator),
            ("types", self.types),
            ("subtypes", self.subtypes),
            ("serializer", self.serializer),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        ]

    @overload
    def update(self, __m, **kwargs):
        # type: (R, SupportsKeysAndGetItem[str, Any], **Any) -> R
        """."""

    @overload
    def update(self, __m, **kwargs):
        # type: (R, Iterable[tuple[str, Any]], **Any) -> R
        """."""

    @overload
    def update(self, **kwargs):
        # type: (R, **Any) -> R
        """."""

    def update(self, *args, **kwargs):
        """
        Make a new relationship with updates.

        Same parameters as :meth:`dict.update`.
        :return: Updated relationship.
        """
        init_args = self.to_dict(usecase=basic_data.ItemUsecase.INIT)
        init_args.update(*args, **kwargs)
        return cast(R, type(self)(**init_args))

    @property
    def converter(self):
        # type: () -> Callable[[Any], T] | Type[T] | str | None
        """Callable value converter."""
        return self._converter

    @property
    def validator(self):
        # type: () -> Callable[[Any], None] | str | None
        """Callable value validator."""
        return self._validator

    @property
    def types(self):
        # type: () -> tuple[Type[T] | str | None, ...]
        """Types for runtime checking."""
        return self._types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self._subtypes

    @property
    def serializer(self):
        # type: () -> Serializer[T] | None
        """Serializer."""
        return self._serializer

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
    def types_info(self):
        # type: () -> RelationshipTypesInfo[T]
        """Information about relationship types."""
        if self._types_info is None:
            self._types_info = RelationshipTypesInfo(self.types, self.extra_paths, self.builtin_paths)
        return self._types_info

    @property
    def will_process(self):
        # type: () -> bool
        """Whether value will be processed or not."""
        return any((self.converter is not None, self.types, self.validator is not None))


R = TypeVar("R", bound=Relationship)


class RelationshipTypesInfo(basic_data.ImmutableBasicData, Generic[T]):
    """Information about relationship types."""

    __slots__ = (
        "_input_types",
        "_all_types",
        "_basic_types",
        "_complex_types",
        "_mapping_types",
        "_iterable_types",
    )

    def __init__(self, input_types=(), extra_paths=(), builtin_paths=None):
        # type: (tuple[Type[T] | str | None, ...], Iterable[str], Iterable[str] | None) -> None
        """
        :param input_types: Input types.
        """
        self._input_types = input_types

        # Import and gather types.
        self._all_types = cast(
            Tuple[Type[T], ...],
            type_checking.import_types(
                input_types,
                extra_paths=extra_paths,
                builtin_paths=builtin_paths,
            ),
        )
        self._basic_types = cast(Tuple[Type[T], ...], tuple(t for t in self._all_types if t in BASIC_TYPES))
        self._complex_types = cast(Tuple[Type[T], ...], tuple(t for t in self._all_types if t not in BASIC_TYPES))

        # Gather mapping types.
        mapping_types = []
        for typ in self._complex_types:
            try:
                origin = get_origin(typ)
            except (TypeError, ValueError):
                pass
            else:
                if origin is not None:
                    typ = origin
            if isinstance(typ, type) and issubclass(typ, Mapping):
                mapping_types.append(typ)
        self._mapping_types = cast(Tuple[Type[T], ...], tuple(mapping_types))

        # Gather iterable types (non-string, non-mapping).
        iterable_types = []
        for typ in self._complex_types:
            try:
                origin = get_origin(typ)
            except (TypeError, ValueError):
                pass
            else:
                if origin is not None:
                    typ = origin
            if (
                isinstance(typ, type)
                and not issubclass(typ, six.string_types)
                and not issubclass(typ, Mapping)
                and issubclass(typ, Iterable)
            ):
                iterable_types.append(typ)
            self._iterable_types = cast(Tuple[Type[T], ...], tuple(iterable_types))

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
        """
        Convert to items.

        :param usecase: Usecase.
        :return: Items.
        """
        return [("input_types", self.input_types)]

    @overload
    def update(self, __m, **kwargs):
        # type: (RTI, SupportsKeysAndGetItem[str, Any], **Any) -> RTI
        """."""

    @overload
    def update(self, __m, **kwargs):
        # type: (RTI, Iterable[tuple[str, Any]], **Any) -> RTI
        """."""

    @overload
    def update(self, **kwargs):
        # type: (RTI, **Any) -> RTI
        """."""

    def update(self, *args, **kwargs):
        """
        Make a new type info with updates.

        Same parameters as :meth:`dict.update`.
        :return: Updated type info.
        """
        init_args = self.to_dict(usecase=basic_data.ItemUsecase.INIT)
        init_args.update(*args, **kwargs)
        return cast(RTI, type(self)(**init_args))

    @property
    def input_types(self):
        # type: () -> tuple[Type[T] | str | None, ...]
        """Input types."""
        return self._input_types

    @property
    def all_types(self):
        # type: () -> tuple[Type[T], ...]
        """All types."""
        return self._all_types

    @property
    def basic_types(self):
        # type: () -> tuple[Type[T], ...]
        """Basic types."""
        return self._basic_types

    @property
    def complex_types(self):
        # type: () -> tuple[Type[T], ...]
        """Complex types."""
        return self._complex_types

    @property
    def mapping_types(self):
        # type: () -> tuple[Type[T], ...]
        """Mapping types."""
        return self._mapping_types

    @property
    def iterable_types(self):
        # type: () -> tuple[Type[T], ...]
        """Iterable types."""
        return self._iterable_types


RTI = TypeVar("RTI", bound=RelationshipTypesInfo)
