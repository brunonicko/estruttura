from basicco import type_checking, recursive_repr, fabricate_value, custom_repr, import_path
from tippo import Any, Callable, Type, Iterable, Generic, TypeVar, cast

from .bases import BaseGeneric


T = TypeVar("T")


class BaseRelationship(BaseGeneric, Generic[T]):
    """Describes a relationship between a structure and its values."""

    __slots__ = (
        "__converter",
        "__types",
        "__subtypes",
        "__repr",
        "__eq",
        "__hash",
        "__metadata",
        "__extra_paths",
        "__builtin_paths",
    )

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[BRT], dict[str, Any]) -> BRT
        extra_paths = serialized["extra_paths"]
        builtin_paths = serialized["builtin_paths"]
        return cls(
            converter=import_path.import_path(
                serialized["converter"], extra_paths=extra_paths, builtin_paths=builtin_paths
            ),
            types=(
                import_path.import_path(t, extra_paths=extra_paths, builtin_paths=builtin_paths)
                for t in serialized["types"]
            ),
            subtypes=serialized["subtypes"],
            repr=serialized["repr"],
            eq=serialized["eq"],
            hash=serialized["hash"],
            metadata=serialized["metadata"],
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        )

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        types=(),  # type: Iterable[Type[T] | Type | str | None] | Type[T] | Type | str | None
        subtypes=False,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
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

        self.__converter = fabricate_value.format_factory(converter)
        self.__types = type_checking.format_types(types)
        self.__subtypes = bool(subtypes)
        self.__repr = bool(repr)
        self.__eq = bool(eq)
        self.__hash = bool(hash)
        self.__metadata = metadata
        self.__extra_paths = tuple(extra_paths)
        self.__builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None

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
            self.__converter,
            value,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def accepts_type(self, value):
        # type: (Any) -> bool
        return type_checking.is_instance(
            value,
            self.__types,
            subtypes=self.__subtypes,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def check_type(self, value):
        # type: (Any) -> T
        if self.__types:
            return type_checking.assert_is_instance(
                value,
                self.__types,
                subtypes=self.__subtypes,
                extra_paths=self.__extra_paths,
                builtin_paths=self.__builtin_paths,
            )
        else:
            return value

    def process(self, value):
        # type: (Any) -> T
        return self.check_type(self.convert(value))

    def to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return (
            ("converter", self.converter),
            ("types", self.types),
            ("subtypes", self.subtypes),
            ("repr", self.repr),
            ("eq", self.eq),
            ("hash", self.hash),
            ("metadata", self.metadata),
            ("extra_paths", self.extra_paths),
            ("builtin_paths", self.builtin_paths),
        )

    def to_dict(self):
        # type: () -> dict[str, Any]
        return dict(self.to_items())

    def serialize(self):
        # type: () -> dict[str, Any]
        extra_paths = self.__extra_paths
        builtin_paths = self.__builtin_paths
        return dict(
            converter=import_path.get_path(self.__converter, extra_paths=extra_paths, builtin_paths=builtin_paths),
            types=[import_path.get_path(t, extra_paths=extra_paths, builtin_paths=builtin_paths) for t in self.__types],
            subtypes=self.__subtypes,
            repr=self.__repr,
            eq=self.__eq,
            hash=self.__hash,
            metadata=self.__metadata,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def update(self, *args, **kwargs):
        # type: (BRT, **Any) -> BRT
        updated_kwargs = self.to_dict()
        updated_kwargs.update(*args, **kwargs)
        return cast(BRT, type(self)(**updated_kwargs))

    @property
    def converter(self):
        # type: () -> Callable[[Any], T] | Type[T] | str | None
        return self.__converter

    @property
    def types(self):
        # type: () -> tuple[Type | str, ...]
        """Types for runtime checking."""
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self.__subtypes

    @property
    def repr(self):
        # type: () -> bool
        """Whether to include in the `__repr__` method."""
        return self.__repr

    @property
    def eq(self):
        # type: () -> bool
        """Whether to include in the `__eq__` method."""
        return self.__eq

    @property
    def hash(self):
        # type: () -> bool
        """Whether to include in the `__hash__` method."""
        return self.__hash

    @property
    def metadata(self):
        # type: () -> Any
        """User metadata."""
        return self.__metadata

    @property
    def extra_paths(self):
        # type: () -> tuple[str, ...]
        """Extra module paths in fallback order."""
        return self.__extra_paths

    @property
    def builtin_paths(self):
        # type: () -> tuple[str, ...] | None
        """Builtin module paths in fallback order."""
        return self.__builtin_paths


BRT = TypeVar("BRT", bound=BaseRelationship)
