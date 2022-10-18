from ..base import BaseAttribute, BaseMutableAttribute


class StateAttribute(BaseAttribute):
    __slots__ = ()


class MutableStateAttribute(StateAttribute, BaseMutableAttribute):
    __slots__ = ()
