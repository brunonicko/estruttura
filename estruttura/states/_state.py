import abc

from basicco import runtime_final
from tippo import Any, Type, Generic, TypeVar, cast

from estruttura.bases import BaseHashable, BaseInteractiveCollection


T = TypeVar("T")  # contained value type
IT = TypeVar("IT")  # internal type


class State(BaseHashable, BaseInteractiveCollection[T], Generic[T, IT]):
    """Base immutable state."""

    __slots__ = ("__hash", "__internal")

    @staticmethod
    def __new__(cls, initial=None):
        if type(initial) is cls:
            return initial
        else:
            return super(State, cls).__new__(cls)

    @classmethod
    @runtime_final.final
    def _make(cls, internal):
        # type: (Type[S], IT) -> S
        """
        Build new state by directly setting the internal value.

        :param internal: Internal state.
        :return: State.
        """
        self = cast(S, cls.__new__(cls))
        self.__internal = internal
        self.__hash = None
        return self

    @staticmethod
    @abc.abstractmethod
    def _init_internal(initial):
        # type: (Any) -> IT
        """Initialize internal."""
        raise NotImplementedError()

    @abc.abstractmethod
    def __init__(self, initial=None):
        self.__internal = self._init_internal(initial=initial)
        self.__hash = None  # type: int | None

    @runtime_final.final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(self._internal)
        return self.__hash

    @runtime_final.final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if isinstance(other, type(self)):
            return self.__internal == other.__internal
        try:
            hash(other)
        except TypeError:
            return self.__internal == other
        else:
            return False

    @runtime_final.final
    def __copy__(self):
        # type: (S) -> S
        """
        Get itself.

        :return: Itself.
        """
        return self

    @property
    @runtime_final.final
    def _internal(self):
        # type: () -> Any
        """Internal values."""
        return self.__internal


S = TypeVar("S", bound=State)  # state type
