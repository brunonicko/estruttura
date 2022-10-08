import itertools

import pyrsistent
from basicco import recursive_repr, custom_repr, safe_repr
from tippo import Any, TypeVar, Iterable, Iterator, Type, overload
from pyrsistent.typing import PVector

from estruttura import ListStructure, PrivateListStructure, InteractiveListStructure, get_relationship

from ._bases import UniformData, PrivateUniformData, InteractiveUniformData


T = TypeVar("T")  # value type


# noinspection PyAbstractClass
class ProtectedDataList(UniformData[PVector[T], T], ListStructure[T]):
    """Protected data list."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Iterable[T]) -> PVector[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pvector(initial or ())

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None

        rel = get_relationship(self)
        if rel is not None:
            initial = tuple(rel.process(v) for v in initial)

        super(ProtectedDataList, self).__init__(initial)

    @classmethod
    def __construct__(cls, values):
        # type: (Type[PRDL], list[T]) -> PRDL
        """
        Construct an instance with deserialized values.

        :param values: Deserialized values.
        :return: Instance.
        """
        return cls(values)

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
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

    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__qualname__),
            suffix="])",
        )

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._internal)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> list[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.
        :param index: Index/slice.
        :return: Value/values.
        """
        if isinstance(index, slice):
            return list(self._internal[index])
        else:
            return self._internal[index]

    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return self._internal.count(value)

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
        if start is None and stop is None:
            args = (value,)  # type: tuple[Any, ...]
        elif start is not None and stop is None:
            args = (value, start)
        elif start is not None and stop is not None:
            args = (value, start, stop)
        else:
            error = "provided 'stop' argument but did not provide 'start'"
            raise ValueError(error)
        return self._internal.index(*args)


PRDL = TypeVar("PRDL", bound=ProtectedDataList)


class PrivateDataList(ProtectedDataList[T], PrivateUniformData[PVector[T], T], PrivateListStructure[T]):
    """Private data list."""

    __slots__ = ()

    def _insert(self, index, *values):
        # type: (PDL, int, T) -> PDL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)

        index = self.resolve_index(index, clamp=True)

        rel = get_relationship(self)
        if rel is not None:
            values = tuple(rel.process(v) for v in values)

        if index == len(self._internal):
            return self._extend(values)
        elif index == 0:
            return self._make(pyrsistent.pvector(values) + self._internal)
        else:
            return self._make(self._internal[:index] + pyrsistent.pvector(values) + self._internal[index:])

    def _move(self, item, target_index):
        # type: (PDL, slice | int, int) -> PDL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        result = self.pre_move(item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        values = self._internal[index:stop]
        internal = self._internal.delete(index, stop)

        if post_index == len(internal):
            return self._make(internal.extend(values))
        elif post_index == 0:
            return self._make(pyrsistent.pvector(values) + internal)
        else:
            return self._make(internal[:post_index] + pyrsistent.pvector(values) + internal[post_index:])

    def _delete(self, item):
        # type: (PDL, slice | int) -> PDL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            return self._make(self._internal.delete(index, stop))
        else:
            index = self.resolve_index(item)
            return self._make(self._internal.delete(index, None))

    @overload
    def _update(self, item, value):
        # type: (PDL, int, T) -> PDL
        pass

    @overload
    def _update(self, item, value):
        # type: (PDL, slice, Iterable[T]) -> PDL
        pass

    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            values = value
        else:
            index = self.resolve_index(item)
            stop = self.resolve_index(item) + 1
            values = (value,)

        rel = get_relationship(self)
        if rel is not None:
            values = tuple(rel.process(v) for v in values)

        pairs = itertools.chain.from_iterable(zip(range(index, stop), values))
        new_internal = self._internal.mset(*pairs)  # type: ignore
        return self._make(new_internal)


PDL = TypeVar("PDL", bound=PrivateDataList)


class DataList(PrivateDataList[T], InteractiveUniformData[PVector[T], T], InteractiveListStructure[T]):
    """Data list."""

    __slots__ = ()
