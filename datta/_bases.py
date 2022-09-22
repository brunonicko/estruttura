import abc

from basicco import state, runtime_final
from tippo import TypeVar, Hashable

from estruttura import BaseMeta, BaseHashable


T_co = TypeVar("T_co", covariant=True)  # covariant value type
IT = TypeVar("IT", bound=Hashable)  # internal type


class BaseDataMeta(BaseMeta):
    """Metaclass for :class:`BaseData`."""


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

    @runtime_final.final
    def __copy__(self):
        cls = type(self)
        self_copy = object.__new__(cls)
        state.update_state(self_copy, state.get_state(self))
        return self_copy
