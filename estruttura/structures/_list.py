from tippo import Any, TypeVar, Iterator, MutableSequence, Iterable, Union, overload

from ..base import BaseList, BaseImmutableList, BaseMutableList
from ._base import CollectionStructure, ImmutableCollectionStructure, MutableCollectionStructure


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

LST = TypeVar("LST", bound=Union[BaseImmutableList, BaseMutableList])  # list state type


class ListStructure(CollectionStructure[LST, T], BaseList[T]):
    __slots__ = ()

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._state[index]

    def __iter__(self):
        # type: () -> Iterator[T]
        for v in iter(self._state):
            yield v

    def __contains__(self, content):
        # type: (object) -> bool
        return content in self._state

    def __len__(self):
        # type: () -> int
        return len(self._state)

    def _insert(self, index, *values):
        # type: (LS, int, T) -> LS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        relationship = type(self).relationship
        if relationship is not None and relationship.will_process:
            values = tuple(relationship.process(v) for v in values)
        return self._transform(self._state.insert(index, *values))

    def _move(self, item, target_index):
        # type: (LS, slice | int, int) -> LS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._transform(self._state.move(item, target_index))

    def _delete(self, item):
        # type: (LS, slice | int) -> LS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._transform(self._state.delete(item))

    @overload
    def _update(self, item, value):
        # type: (LS, int, T) -> LS
        pass

    @overload
    def _update(self, item, value):
        # type: (LS, slice, Iterable[T]) -> LS
        pass

    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        relationship = type(self).relationship
        if relationship is not None and relationship.will_process:
            if isinstance(item, slice):
                value = tuple(relationship.process(v) for v in value)
            else:
                value = relationship.process(value)
        return self._transform(self._state.update(item, value))

    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return self._state.count(value)

    def index(self, value, start=None, stop=None):
        # type: (Any, int | None, int | None) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._state.index(value, start=start, stop=stop)


LS = TypeVar("LS", bound=ListStructure)  # list structure self type


ILST = TypeVar("ILST", bound=BaseImmutableList)  # immutable list state type


class ImmutableListStructure(
    ListStructure[ILST, T_co],
    ImmutableCollectionStructure[ILST, T_co],
    BaseImmutableList[T_co],
):
    __slots__ = ()


class MutableListStructure(
    ListStructure[LST, T_co],
    MutableCollectionStructure[LST, T_co],
    BaseMutableList[T_co],
):
    __slots__ = ()
