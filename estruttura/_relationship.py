"""Relationship between structures and values."""

import six
from basicco import basic_data, fabricate_value, type_checking
from tippo import (
    Any,
    Callable,
    Generic,
    Iterable,
    SupportsKeysAndGetItem,
    Type,
    TypeVar,
    cast,
    overload,
)

from .constants import MISSING
from .exceptions import (
    ConversionError,
    InvalidTypeError,
    ProcessingError,
    ValidationError,
)
from .serialization import Deserializer, Serializer, TypedSerializer

T = TypeVar("T")


class Relationship(basic_data.ImmutableBasicData, Generic[T]):
    """Describes a relationship between a structure and its values."""

    __slots__ = (
        "_converter",
        "_validator",
        "_types",
        "_subtypes",
        "_serializer",
        "_deserializer",
        "_extra_paths",
        "_builtin_paths",
    )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        validator=None,  # type: Callable[[Any], None] | str | None
        types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
        subtypes=False,  # type: bool
        serializer=Serializer,  # type: Type[TypedSerializer] | Callable[[T], Any] | str | None
        deserializer=Deserializer,  # type: Type[TypedSerializer] | Callable[[Any], T] | str | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param validator: Callable value validator.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param serializer: Callable value serializer or typed serializer type.
        :param deserializer: Callable value deserializer or typed deserializer type.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        self._converter = fabricate_value.format_factory(converter)
        self._validator = fabricate_value.format_factory(validator)
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

        if isinstance(serializer, type) and issubclass(serializer, TypedSerializer):
            serializer = serializer(self.types, self.subtypes, self.extra_paths, self.builtin_paths)
        if isinstance(deserializer, type) and issubclass(deserializer, TypedSerializer):
            deserializer = deserializer(self.types, self.subtypes, self.extra_paths, self.builtin_paths)

        self._serializer = fabricate_value.format_factory(serializer)  # type: Callable[[T], Any] | str | None
        self._deserializer = fabricate_value.format_factory(deserializer)  # type: Callable[[Any], T] | str | None

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
        """
        return fabricate_value.fabricate_value(
            self.serializer,
            value,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

    def deserialize_value(self, serialized):
        # type: (Any) -> T
        """
        Deserialize value.

        :param serialized: Serialized value.
        :return: Value.
        """
        return fabricate_value.fabricate_value(
            self.deserializer,
            serialized,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

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
            ("deserializer", self.deserializer),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        ]

    @overload
    def update(self, __m, **kwargs):
        # type: (R, SupportsKeysAndGetItem[str, Any], **Any) -> R
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (R, Iterable[tuple[str, Any]], **Any) -> R
        pass

    @overload
    def update(self, **kwargs):
        # type: (R, **Any) -> R
        pass

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
        # type: () -> Callable[[T], Any] | str | None
        """Callable value serializer."""
        return self._serializer

    @property
    def deserializer(self):
        # type: () -> Callable[[Any], T] | str | None
        """Callable value deserializer."""
        return self._deserializer

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
    def will_process(self):
        # type: () -> bool
        """Whether value will be processed or not."""
        return any((self.converter is not None, self.types, self.validator is not None))


R = TypeVar("R", bound=Relationship)
