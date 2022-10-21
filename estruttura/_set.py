import six
import slotted
from tippo import AbstractSet, Iterable, TypeVar
from basicco.runtime_final import final
from basicco.abstract_class import abstract

from ._base import CollectionStructure, ImmutableCollectionStructure, MutableCollectionStructure
from ._relationship import Relationship
from .exceptions import ProcessingError


T = TypeVar("T")
RT = TypeVar("RT", bound=Relationship)


class SetStructure(CollectionStructure[RT, T], slotted.SlottedSet[T]):
    __slots__ = ()

    @final
    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        initial_values = frozenset(initial)
        if self.relationship is not None and self.relationship.will_process:
            try:
                initial_values = frozenset(self.relationship.process_value(v) for v in initial_values)
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        self._do_init(initial_values)

    @final
    def __le__(self, other):
        # type: (AbstractSet) -> bool
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

    @final
    def __lt__(self, other):
        # type: (AbstractSet) -> bool
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

    @final
    def __gt__(self, other):
        # type: (AbstractSet) -> bool
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

    @final
    def __ge__(self, other):
        # type: (AbstractSet) -> bool
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

    @final
    def __and__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.intersection(other)

    @final
    def __rand__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        return self.__and__(other)

    @final
    def __sub__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :return: Difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.difference(other)

    @final
    def __rsub__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :return: Inverse difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    @final
    def __or__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.union(other)

    @final
    def __ror__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        return self.__or__(other)

    @final
    def __xor__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    @final
    def __rxor__(self, other):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        return self.__xor__(other)

    @abstract
    def _do_init(self, initial_values):
        # type: (frozenset[T]) -> None
        """
        Initialize values.

        :param initial_values: New values.
        """
        raise NotImplementedError()

    @final
    def _add(self, value):
        # type: (SS, T) -> SS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._update((value,))

    @abstract
    def _do_remove(self, old_values):
        # type: (SS, frozenset[T]) -> SS
        """
        Remove values.

        :param old_values: Old values.
        :return: Transformed.
        """
        raise NotImplementedError()

    @final
    def _remove(self, *values):
        # type: (SS, T) -> SS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        old_values = frozenset(values)
        if not old_values:
            return self

        missing = old_values.difference(old_values.intersection(self))
        if len(missing) == 1:
            raise KeyError(next(iter(missing)))
        elif missing:
            raise KeyError(tuple(missing))

        return self._do_remove(old_values)

    @final
    def _discard(self, *values):
        # type: (SS, T) -> SS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        """
        if not values:
            return self

        old_values = frozenset(values).intersection(self)
        if not old_values:
            return self

        return self._do_remove(old_values)

    @abstract
    def _do_update(self, new_values):
        # type: (SS, frozenset[T]) -> SS
        """
        Add values.

        :param new_values: New values.
        :return: Transformed.
        """
        raise NotImplementedError()

    @final
    def _update(self, iterable):
        # type: (SS, Iterable[T]) -> SS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        if self.relationship is not None and self.relationship.will_process:
            try:
                new_values = frozenset(self.relationship.process_value(v) for v in iterable)
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        else:
            new_values = frozenset(iterable)

        new_values = frozenset(self.difference(new_values))
        if not new_values:
            return self

        return self._do_update(new_values)

    @abstract
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        raise NotImplementedError()

    @abstract
    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        raise NotImplementedError()

    @abstract
    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        raise NotImplementedError()

    @abstract
    def intersection(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        raise NotImplementedError()

    @abstract
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        raise NotImplementedError()

    @abstract
    def union(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        raise NotImplementedError()

    @abstract
    def difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        raise NotImplementedError()

    @abstract
    def inverse_difference(self, iterable):
        # type: (Iterable) -> AbstractSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        raise NotImplementedError()


SS = TypeVar("SS", bound=SetStructure)  # set structure self type


# noinspection PyAbstractClass
class ImmutableSetStructure(SetStructure[RT, T], ImmutableCollectionStructure[RT, T]):
    __slots__ = ()

    @final
    def add(self, value):
        # type: (ISS, T) -> ISS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._add(value)

    @final
    def discard(self, *values):
        # type: (ISS, T) -> ISS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        """
        return self._discard(*values)

    @final
    def remove(self, *values):
        # type: (ISS, T) -> ISS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._remove(*values)

    @final
    def update(self, iterable):
        # type: (ISS, Iterable[T]) -> ISS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._update(iterable)


ISS = TypeVar("ISS", bound=ImmutableSetStructure)  # immutable set structure self type


# noinspection PyAbstractClass
class MutableSetStructure(SetStructure[RT, T], MutableCollectionStructure[RT, T], slotted.SlottedMutableSet[T]):
    __slots__ = ()

    @final
    def __iand__(self, iterable):
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.intersection_update(iterable)
        return self

    @final
    def __isub__(self, iterable):
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.difference(iterable)
        return self

    @final
    def __ior__(self, iterable):
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.update(iterable)
        return self

    @final
    def __ixor__(self, iterable):
        """
        Symmetric difference in place: `self ^= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        if iterable is self:
            self.clear()
        else:
            self.symmetric_difference_update(iterable)
        return self

    @final
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        :raises KeyError: Empty set.
        """
        value = next(iter(self))
        self.remove(value)
        return value

    @final
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        difference = self.difference(iterable)
        if difference:
            self.remove(*difference)

    @final
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        inverse_difference = self.inverse_difference(iterable)
        intersection = self.intersection(iterable)
        if inverse_difference:
            self._update(inverse_difference)
        if intersection:
            self.remove(*intersection)

    @final
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        intersection = self.intersection(iterable)
        if intersection:
            self.remove(*intersection)

    @final
    def add(self, value):
        # type: (T) -> None
        """
        Add value.

        :param value: Value.
        """
        self.add(value)

    @final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        """
        self.discard(*values)

    @final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :raises KeyError: Value is not present.
        """
        self.remove(*values)

    @final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self.update(iterable)
