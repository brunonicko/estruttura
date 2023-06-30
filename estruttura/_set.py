from basicco import abstract
from basicco.custom_repr import iterable_repr
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from slotted import SlottedMutableSet, SlottedSet
from tippo import AbstractSet, Any, Hashable, Iterable, TypeVar

from ._base import CollectionStructure, ImmutableCollectionStructure
from ._base import MutableCollectionStructure

__all__ = ["SetStructure", "ImmutableSetStructure", "MutableSetStructure"]


T = TypeVar("T")


class SetStructure(CollectionStructure[T], SlottedSet[T]):
    """Abstract Set Structure."""

    __slots__ = ()

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return iterable_repr(
            self,
            prefix="{}({{".format(type(self).__name__),
            suffix="})",
        )

    @abstract
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if not isinstance(other, AbstractSet):
            return False
        if type(self) is not type(other):
            return (
                not isinstance(self, Hashable) or not isinstance(other, Hashable)
            ) and set(self) == set(other)
        return set(self) == set(other)  # noqa

    def __le__(self, other):
        # type: (AbstractSet[Any]) -> bool
        """
        Less equal operator (self <= other).

        :param other: Another set or any object.
        :return: True if considered less equal.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__le__(other)

    def __lt__(self, other):
        # type: (AbstractSet[Any]) -> bool
        """
        Less than operator: `self < other`.

        :param other: Another set or any object.
        :return: True if considered less than.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__lt__(other)

    def __gt__(self, other):
        # type: (AbstractSet[Any]) -> bool
        """
        Greater than operator: `self > other`.

        :param other: Another set or any object.
        :return: True if considered greater than.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__gt__(other)

    def __ge__(self, other):
        # type: (AbstractSet[Any]) -> bool
        """
        Greater equal operator: `self >= other`.

        :param other: Another set or any object.
        :return: True if considered greater equal.
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__ge__(other)

    def __and__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.intersection(other)

    def __rand__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        return self.__and__(other)

    def __sub__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :return: Difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.difference(other)

    def __rsub__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :return: Inverse difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    def __or__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.union(other)

    def __ror__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        return self.__or__(other)

    def __xor__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    def __rxor__(self, other):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        return self.__xor__(other)

    def isdisjoint(self, iterable):
        # type: (Iterable[Any]) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return set(self).isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable[Any]) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return set(self).issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable[Any]) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return set(self).issuperset(iterable)

    @abstract
    def intersection(self, iterable):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        raise NotImplementedError()

    @abstract
    def symmetric_difference(self, iterable):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        raise NotImplementedError()

    @abstract
    def union(self, iterable):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        raise NotImplementedError()

    @abstract
    def difference(self, iterable):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        raise NotImplementedError()

    @abstract
    def inverse_difference(self, iterable):
        # type: (Iterable[Any]) -> AbstractSet[Any]
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        raise NotImplementedError()


SS = TypeVar("SS", bound=SetStructure[Any])


class ImmutableSetStructure(ImmutableCollectionStructure[T], SetStructure[T]):
    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        return hash(frozenset(self))

    @abstract
    def update(self, iterable):
        # type: (ISS, Iterable[T]) -> ISS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstract
    def discard(self, *value):
        # type: (ISS, *T) -> ISS
        """
        Discard value(s).

        :param value: Value(s).
        :return: Transformed.
        """
        raise NotImplementedError()

    def add(self, *value):
        # type: (ISS, *T) -> ISS
        """
        Add value(s).

        :param value: Value(s).
        :return: Transformed.
        """
        return self.update(value)

    def remove(self, *value):
        # type: (ISS, *T) -> ISS
        """
        Remove value(s).

        :param value: Value(s).
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        for v in value:
            if v not in self:
                raise KeyError(v)
        return self.discard(*value)


ISS = TypeVar("ISS", bound=ImmutableSetStructure[Any])


class MutableSetStructure(
    MutableCollectionStructure[T],
    SetStructure[T],
    SlottedMutableSet[T],
):
    __slots__ = ()

    __hash__ = None  # type: ignore

    def __iand__(self, iterable):
        # type: (MSS, Iterable[Any]) -> MSS
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :return: Self.
        """
        self.intersection_update(iterable)
        return self

    def __isub__(self, iterable):
        # type: (MSS, Iterable[Any]) -> MSS
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :return: Self.
        """
        self.difference(iterable)
        return self

    def __ior__(self, iterable):
        # type: (MSS, Iterable[Any]) -> MSS
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :return: Self.
        """
        self.update(iterable)
        return self

    def __ixor__(self, iterable):
        # type: (MSS, Iterable[Any]) -> MSS
        """
        Symmetric difference in place: `self ^= iterable`.

        :param iterable: Iterable.
        :return: Self.
        """
        if iterable is self:
            self.clear()
        else:
            self.symmetric_difference_update(iterable)
        return self

    @abstract
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @abstract
    def discard(self, *value):
        # type: (*T) -> None
        """
        Discard value(s).

        :param value: Value(s).
        """
        raise NotImplementedError()

    def add(self, *value):
        # type: (*T) -> None
        """
        Add value(s).

        :param value: Value(s).
        """
        self.update(value)

    def remove(self, *value):
        # type: (*T) -> None
        """
        Remove value(s).

        :param value: Value(s).
        :raises KeyError: Value is not present.
        """
        for v in value:
            if v not in self:
                raise KeyError(v)
        return self.discard(*value)

    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        :raises KeyError: Empty set.
        """
        try:
            value = next(iter(self))
        except StopIteration:
            pass
        else:
            self.discard(value)
            return value
        raise KeyError("empty set")

    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        difference = self.difference(iterable)
        if difference:
            self.discard(*difference)

    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        inverse_difference = self.inverse_difference(iterable)
        intersection = self.intersection(iterable)
        if inverse_difference:
            self.update(inverse_difference)
        if intersection:
            self.discard(*intersection)

    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        intersection = self.intersection(iterable)
        if intersection:
            self.discard(*intersection)


MSS = TypeVar("MSS", bound=MutableSetStructure[Any])
