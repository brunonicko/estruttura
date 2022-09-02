import slotted
from basicco import type_checking, import_path, recursive_repr, fabricate_value, custom_repr
from tippo import Any, Callable, Type, Iterable, TypeVar


T = TypeVar("T")
RT = TypeVar("RT", bound="Relationship")


class Relationship(slotted.SlottedABC):
    """Describes a relationship between a structure and its values."""

    __slots__ = (
        "__weakref__",
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
        # type: (Type[RT], dict[str, Any]) -> RT
        kwargs = {}

        extra_paths = kwargs["extra_paths"] = serialized.get("extra_paths", ())
        builtin_paths = kwargs["builtin_paths"] = serialized.get("builtin_paths", None)

        if "converter" in serialized:
            kwargs["converter"] = import_path.import_path(
                serialized["converter"],
                extra_paths=extra_paths,
                builtin_paths=builtin_paths,
            )

        if "types" in serialized:
            kwargs["types"] = (
                import_path.import_path(t, extra_paths=extra_paths, builtin_paths=builtin_paths)
                for t in serialized["types"]
            )

        if "subtypes" in serialized:
            kwargs["subtypes"] = serialized["subtypes"]

        if "repr" in serialized:
            kwargs["repr"] = serialized["repr"]

        if "eq" in serialized:
            kwargs["eq"] = serialized["eq"]

        if "hash" in serialized:
            kwargs["hash"] = serialized["hash"]

        if "metadata" in serialized:
            kwargs["metadata"] = serialized["metadata"]

        return cls(**kwargs)

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        types=(),  # type: tuple[Type[T] | Type | str | None, ...] | Type[T] | Type | str | None
        subtypes=False,  # type: bool
        repr=True,  # type: bool
        eq=True,  # type: bool
        hash=None,  # type: bool | None
        # serializer=None,  # type: Callable | str | None
        # deserializer=None,  # type: Callable | str | None
        metadata=None,  # type: Any
        # metadata_serializer=None,  # type: Callable | str | None
        # metadata_deserializer=None,  # type: Callable | str | None
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

        self.__converter = converter
        self.__types = type_checking.format_types(types)
        self.__subtypes = bool(subtypes)
        self.__repr = bool(repr)
        self.__eq = bool(eq)
        self.__hash = bool(hash)
        self.__extra_paths = tuple(extra_paths)
        self.__builtin_paths = tuple(builtin_paths) if builtin_paths is not None else None
        self.__metadata = metadata

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def convert(self, value):
        # type: (Any) -> T
        return fabricate_value.fabricate_value(
            self.__converter,
            value,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

    def type_matches(self, value):
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
        return type_checking.assert_is_instance(
            value,
            self.__types,
            subtypes=self.__subtypes,
            extra_paths=self.__extra_paths,
            builtin_paths=self.__builtin_paths,
        )

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
        serialized = {}  # type: dict[str, Any]

        if self.__converter is not None:
            serialized["converter"] = import_path.get_path(self.__converter)

        if self.__types:
            serialized["types"] = [import_path.get_path(t) for t in self.__types]

        if self.__subtypes:
            serialized["subtypes"] = self.__subtypes

        if not self.__repr:
            serialized["repr"] = self.__repr

        if not self.__eq:
            serialized["eq"] = self.__eq

        if not self.__hash:
            serialized["hash"] = self.__hash

        if self.__metadata is not None:
            serialized["metadata"] = self.__metadata

        if self.__extra_paths:
            serialized["extra_paths"] = list(self.__extra_paths)

        if self.__builtin_paths is not None:
            serialized["builtin_paths"] = list(self.__builtin_paths)

        return serialized

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
