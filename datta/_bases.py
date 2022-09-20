import abc

from basicco import runtime_final
from tippo import Any, Type, Generic, TypeVar, Hashable, cast

from estruttura import BaseHashable, BasePrivateCollection, BaseInteractiveCollection


T_co = TypeVar("T_co", covariant=True)  # covariant value type
IT = TypeVar("IT", bound=Hashable)  # internal type


class BaseData(BaseHashable):
    """Base data."""

    __slots__ = ("__hash",)

    @abc.abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()


class BasePrivateDataCollection(BasePrivateCollection[T_co], BaseData, Generic[IT, T_co]):
    """Base private data collection."""

    __slots__ = ("__hash", "__internal")

    @staticmethod
    @runtime_final.final
    def __new__(cls, initial=None, *args, **kwargs):
        if type(initial) is cls and not args and not kwargs:
            return initial
        else:
            return super(BasePrivateDataCollection, cls).__new__(cls)

    @classmethod
    @runtime_final.final
    def _make(cls, internal):
        # type: (Type[BPDC], IT) -> BPDC
        """
        Build new state by directly setting the internal value.

        :param internal: Internal state.
        :return: State.
        """
        self = cast(BPDC, cls.__new__(cls))
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
        # type: (BPDC) -> BPDC
        """
        Get itself.

        :return: Itself.
        """
        return self

    @property
    @runtime_final.final
    def _internal(self):
        # type: () -> IT
        """Internal values."""
        return self.__internal


BPDC = TypeVar("BPDC", bound=BasePrivateDataCollection)  # base private data collection type


# noinspection PyAbstractClass
class BaseDataCollection(BasePrivateDataCollection[IT, T_co], BaseInteractiveCollection[T_co]):
    """Base data collection."""

    __slots__ = ()
