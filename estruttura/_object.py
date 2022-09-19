import abc

import six
from basicco import runtime_final
from tippo import Any, Callable, TypeVar, Tuple, Iterable, TypeAlias, Generic, Type

from .bases import (
    BaseAttribute,
    BaseMutableAttribute,
    AttributeMap,
    BaseObjectMeta,
    BaseObject,
    BasePrivateObject,
    BaseInteractiveObject,
    BaseMutableObject,
    MissingType,
    MISSING,
)
from ._dict import DictState
from ._bases import (
    BaseRelationship,
    BaseStructure,
    BasePrivateStructure,
    BaseInteractiveStructure,
    BaseMutableStructure,
)


T = TypeVar("T")  # value type
T_co = TypeVar("T_co", covariant=True)  # covariant value type
RT = TypeVar("RT", bound=BaseRelationship)  # relationship type

Item = Tuple[str, Any]  # type: TypeAlias


class BaseStructureAttribute(BaseAttribute[T_co], Generic[T_co, RT]):
    __slots__ = "_relationship"

    def __init__(
        self,
        default=MISSING,  # type: Any
        factory=MISSING,  # type: Callable[..., T_co] | str | MissingType
        init=True,  # type: bool
        required=True,  # type: bool
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
        relationship=None,  # type: RT | None
    ):
        # type: (...) -> None
        super(BaseStructureAttribute, self).__init__(
            default=default,
            factory=factory,
            init=init,
            required=required,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        )

        if relationship is None:
            relationship = type(self)._make_default_relationship()

        self._relationship = relationship

    @classmethod
    @abc.abstractmethod
    def _make_default_relationship(cls):
        # type: () -> RT
        raise NotImplementedError()

    def _to_items(self):
        # type: () -> tuple[tuple[str, Any], ...]
        return super(BaseStructureAttribute, self)._to_items() + (("relationship", self.relationship),)

    def make_default(self):
        # type: () -> T_co
        value = super(BaseStructureAttribute, self).make_default()
        return self.relationship.process(value)

    @property
    def relationship(self):
        # type: () -> RT
        return self._relationship


class BaseMutableStructureAttribute(BaseStructureAttribute[T, RT], BaseMutableAttribute[T]):
    __slots__ = ()

    @abc.abstractmethod
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> T
        raise NotImplementedError()

    @abc.abstractmethod
    def __set__(self, instance, value):
        # type: (BaseObject, T) -> None
        raise NotImplementedError()

    @abc.abstractmethod
    def __delete__(self, instance, value):
        # type: (BaseObject, T) -> None
        raise NotImplementedError()


class BaseObjectStructureMeta(BaseObjectMeta):
    @property
    @abc.abstractmethod
    def __attributes__(cls):
        # type: () -> AttributeMap[BaseStructureAttribute]
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseObjectStructure(
    six.with_metaclass(BaseObjectStructureMeta, BaseStructure[Item, Any, DictState[str, Any], str, RT], BaseObject)
):
    """Base dict structure."""

    __slots__ = ()

    @runtime_final.final
    def get_value(self, location):
        # type: (str) -> Any
        """
        Get value at location.

        :param location: Location.
        :return: Value.
        :raises KeyError: No value at location.
        """
        return self[location]


# noinspection PyAbstractClass
class BasePrivateObjectStructure(
    BaseObjectStructure[RT],
    BasePrivateStructure[Item, Any, DictState[str, Any], str, RT],
    BasePrivateObject,
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseInteractiveObjectStructure(
    BasePrivateObjectStructure[RT],
    BaseInteractiveStructure[Item, Any, DictState[str, Any], str, RT],
    BaseInteractiveObject,
):
    """Base interactive dict structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableObjectStructure(
    BasePrivateObjectStructure[RT],
    BaseMutableStructure[Item, Any, DictState[str, Any], str, RT],
    BaseMutableObject,
):
    """Base mutable dict structure."""

    __slots__ = ()
