from basicco import type_checking, recursive_repr, fabricate_value, custom_repr
from tippo import Any, Callable, Type, Iterable, Generic, TypeVar, cast

from .bases import BaseHashable


T = TypeVar("T")  # value type


class Relationship(BaseHashable, Generic[T]):
    """Describes a relationship between a structure and its values."""

    __slots__ = (
        "_converter",
        "_types",
        "_subtypes",
        "_repr",
        "_eq",
        "_hash",
        "_serializer",
        "_deserializer",
        "_metadata",
        "_extra_paths",
        "_builtin_paths",
    )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        types=(),  # type: Iterable[Type[T] | Type | str | None] | Type[T] | Type | str | None
        subtypes=False,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
        serializer=None,  # type: Callable[[T], Any] | str | None
        deserializer=None,  # type: Callable[[Any], T] | str | None
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        # type: (...) -> None
        """
        :param converter: Callable value converter.
        :param types: Types for runtime checking.
        :param subtypes: Whether to accept subtypes.
        :param repr: Whether to include in the `__repr__` method.
        :param eq: Whether to include in the `__eq__` method.
        :param hash: Whether to include in the `__hash__` method.
        :param serializer: Callable value serializer.
        :param deserializer: Callable value deserializer.
        :param metadata: User metadata.
        :param extra_paths: Extra module paths in fallback order.
        :param builtin_paths: Builtin module paths in fallback order.
        """

        # Ensure safe hash.
        if hash is None:
            hash = eq
        if hash and not eq:
            error = "can't contribute to the hash if it's not contributing to the eq"
            raise ValueError(error)

        self._converter = fabricate_value.format_factory(converter)
        self._types = type_checking.format_types(types)
        self._subtypes = bool(subtypes)
        self._repr = bool(repr)
        self._eq = bool(eq)
        self._hash = bool(hash)
        self._serializer = fabricate_value.format_factory(serializer)
        self._deserializer = fabricate_value.format_factory(deserializer)
        self._metadata = metadata
        self._extra_paths = tuple(extra_paths)
        self._builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

    @recursive_repr.recursive_repr
    def __repr__(self):
        items = self.to_items()
        return custom_repr.mapping_repr(
            mapping=dict(items),
            prefix="{}(".format(type(self).__name__),
            template="{key}={value}",
            separator=", ",
            suffix=")",
            sorting=True,
            sort_key=lambda i, _s=self, _i=items: next(iter(zip(*_i))).index(i[0]),
            key_repr=str,
        )

    def __hash__(self):
        return hash(self.to_items())

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.to_items() == other.to_items()

    def convert(self, value):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self._converter,
            value,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def accepts_type(self, value):
        # type: (Any) -> bool
        return type_checking.is_instance(
            value,
            self._types,
            subtypes=self._subtypes,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def check_type(self, value):
        # type: (Any) -> T
        if self._types:
            return type_checking.assert_is_instance(
                value,
                self._types,
                subtypes=self._subtypes,
                extra_paths=self._extra_paths,
                builtin_paths=self._builtin_paths,
            )
        else:
            return value

    def process(self, value):
        # type: (Any) -> T
        return self.check_type(self.convert(value))

    def serialize(self, value, *args, **kwargs):
        # type: (T, *Any, **Any) -> Any
        return fabricate_value.fabricate_value(
            self._serializer,
            value,
            args=args,
            kwargs=kwargs,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def deserialize(self, serialized, *args, **kwargs):
        # type: (Any, *Any, **Any) -> T
        return fabricate_value.fabricate_value(
            self._deserializer,
            serialized,
            args=args,
            kwargs=kwargs,
            extra_paths=self._extra_paths,
            builtin_paths=self._builtin_paths,
        )

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("converter", self.converter),
            ("types", self.types),
            ("subtypes", self.subtypes),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("serializer", self.serializer),
            ("deserializer", self.deserializer),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    def update(self, *args, **kwargs):
        # type: (R, **Any) -> R
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(R, type(self)(**updated_kwargs))

    @property
    def converter(self):
        # type: () -> Callable[[Any], T] | Type[T] | str | None
        return self._converter

    @property
    def types(self):
        # type: () -> tuple[Type | str, ...]
        """Types for runtime checking."""
        return self._types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self._subtypes

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


R = TypeVar("R", bound=Relationship)  # relationship type
