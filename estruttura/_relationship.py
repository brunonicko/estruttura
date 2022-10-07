"""Relationships between structures and values."""

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
        serializer=None,  # type: Callable[[T], Any] | str | None
        deserializer=None,  # type: Callable[[Any], T] | str | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param validator: Callable value validator.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param serializer: Callable value serializer.
        :param deserializer: Callable value deserializer.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """
        self._converter = fabricate_value.format_factory(converter)
        self._validator = fabricate_value.format_factory(validator)
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._serializer = fabricate_value.format_factory(serializer)
        self._deserializer = fabricate_value.format_factory(deserializer)
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

    def convert(self, value):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self.converter,
            value,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def validate(self, value):
        # type: (Any) -> T
        fabricate_value.fabricate_value(
            self.validator,
            value,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )
        return value

    def accepts_type(self, value):
        # type: (Any) -> bool
        return type_checking.is_instance(
            value,
            self.types,
            subtypes=self.subtypes,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

    def check_type(self, value):
        # type: (Any) -> T
        if self.types:
            return type_checking.assert_is_instance(
                value,
                self.types,
                subtypes=self.subtypes,
                extra_paths=self.extra_paths,
                builtin_paths=self.builtin_paths,
            )
        else:
            return value

    def process(self, value):
        # type: (Any) -> T
        return self.validate(self.check_type(self.convert(value)))

    def serialize(self, value):
        # type: (T) -> Any
        return fabricate_value.fabricate_value(
            self.serializer,
            value,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

    def deserialize(self, serialized):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self.deserializer,
            serialized,
            extra_paths=self.extra_paths,
            builtin_paths=self.builtin_paths,
        )

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
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


R = TypeVar("R", bound=Relationship)
