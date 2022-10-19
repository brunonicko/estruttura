import pyrsistent
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import iterable_repr
from basicco.explicit_hash import set_to_none
from tippo import Iterable, Iterator, TypeVar, Type, AbstractSet, cast
from pyrsistent.typing import PSet

from ..base import BaseSet, BaseImmutableSet, BaseMutableSet


T = TypeVar("T")


_PSET_TYPE = type(pyrsistent.pset())  # type: Type[PSet]


class SetState(BaseSet[T]):
    __slots__ = ()

    @abstract
    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        raise NotImplementedError()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__qualname__),
            suffix="])",
            sorting=True,
            sort_key=lambda v: id(v),
        )

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Whether value is present.

        :param value: Value.
        :return: True if present.
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._internal:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._internal)

    @property
    @abstract
    def _internal(self):
        # type: () -> AbstractSet[T]
        raise NotImplementedError()


class ImmutableSetState(SetState[T], BaseImmutableSet[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        if type(initial) is _PSET_TYPE:
            internal = cast(PSet[T], initial)
        else:
            internal = pyrsistent.pset(initial)
        self.__internal = internal  # type: PSet[T]

    def __hash__(self):
        # type: () -> int
        return hash(self._internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(ImmutableSetState, other)._internal

    def _clear(self):
        # type: (ISS) -> ISS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        return type(self)()

    def _discard(self, *values):
        # type: (ISS, T) -> ISS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return type(self)(self._internal.difference(values))

    def _update(self, iterable):
        # type: (ISS, Iterable[T]) -> ISS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return type(self)(self._internal.update(iterable))

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._internal.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> ImmutableSetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return type(self)(self._internal.intersection(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> ImmutableSetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return type(self)(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> ImmutableSetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return type(self)(self._internal.union(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> ImmutableSetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return type(self)(self._internal.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable) -> ImmutableSetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        if isinstance(iterable, (set, frozenset, _PSET_TYPE)):
            inverse_difference = iterable.difference(self._internal)
        else:
            inverse_difference = set(iterable).difference(self._internal)
        return type(self)(pyrsistent.pset(inverse_difference))

    @property
    def _internal(self):
        # type: () -> PSet[T]
        return self.__internal


ISS = TypeVar("ISS", bound=ImmutableSetState)


class MutableSetState(SetState[T], BaseMutableSet[T]):
    __slots__ = ("__internal",)

    def __init__(self, initial=()):
        self.__internal = set(initial)  # type: set[T]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(MutableSetState, other)._internal

    def _clear(self):
        # type: (MSS) -> MSS
        """
        Clear.

        :return: Transformed (immutable) or self (mutable).
        """
        self._internal.clear()
        return self

    def _discard(self, *values):
        # type: (MSS, T) -> MSS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self._internal.difference_update(values)
        return self

    def _update(self, iterable):
        # type: (MSS, Iterable[T]) -> MSS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self._internal.update(iterable)
        return self

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._internal.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> MutableSetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return type(self)(self._internal.intersection(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> MutableSetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return type(self)(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> MutableSetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return type(self)(self._internal.union(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> MutableSetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return type(self)(self._internal.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable) -> MutableSetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return type(self)(set(iterable).difference(self._internal))

    @property
    def _internal(self):
        # type: () -> set[T]
        return self.__internal


MSS = TypeVar("MSS", bound=MutableSetState)
