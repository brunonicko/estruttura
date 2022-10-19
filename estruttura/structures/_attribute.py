import six
from basicco.basic_data import ItemUsecase
from tippo import Any, Callable, Type, TypeVar, Iterable

from ..base import BaseAttributeMeta, BaseAttribute, BaseMutableAttributeMeta, BaseMutableAttribute
from ..constants import MissingType, MISSING
from ._relationship import Relationship


T_co = TypeVar("T_co", covariant=True)


class StructureAttributeMeta(BaseAttributeMeta):
    __relationship_type__ = Relationship  # type: Type[Relationship]


class StructureAttribute(six.with_metaclass(StructureAttributeMeta, BaseAttribute[T_co])):
    __slots__ = ("_relationship",)

    def __init__(
        self,
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
        metadata=None,  # type: Any
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
        relationship=None,  # type: Relationship[T_co] | None
    ):
        super(StructureAttribute, self).__init__(
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
            metadata=metadata,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        )
        self._relationship = relationship

    def to_items(self, usecase=None):
        # type: (ItemUsecase | None) -> list[tuple[str, Any]]
        items = super(StructureAttribute, self).to_items(usecase=usecase)
        items.append(("relationship", self.relationship))
        return items

    def process(self, value):
        # type: (Any) -> T_co
        if self.relationship is not None:
            try:
                return self.relationship.process(value)
            except Exception as e:
                exc = type(e)("{!r} attribute; {}".format(self.name, e))
                six.raise_from(exc, None)
                raise exc
        return value

    @property
    def relationship(self):
        # type: () -> Relationship[T_co] | None
        return self._relationship


class MutableStructureAttributeMeta(StructureAttributeMeta, BaseMutableAttributeMeta):
    pass


class MutableStructureAttribute(
    six.with_metaclass(MutableStructureAttributeMeta, StructureAttribute, BaseMutableAttribute)
):
    __slots__ = ()
