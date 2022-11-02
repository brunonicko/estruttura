from ._dict import MutableDict
from estruttura._helpers import dict_attribute as _dict_attribute


def dict_attribute(
    dict_type=MutableDict,
    **kwargs,
):
    return _dict_attribute(dict_type=dict_type, **kwargs)
