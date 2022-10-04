from basicco import type_checking
from tippo import Any, Mapping

from datta import DataList, DataDict, DataRelationship

__all__ = ["JSONList", "JSONDict"]


JSONTypes = ("datta.examples.JSONList", "datta.examples.JSONDict", str, int, float, bool, None)


def json_converter(value):
    if isinstance(value, Mapping):
        return JSONDict(value)
    elif type_checking.is_iterable(value):
        return JSONList(value)
    else:
        return value


json_relationship = DataRelationship(types=JSONTypes, converter=json_converter)


class JSONList(DataList):
    __kwargs__ = {"relationship": json_relationship}  # type: dict[str, Any]


class JSONDict(DataDict[str, Any]):
    __kwargs__ = {"relationship": json_relationship}  # type: dict[str, Any]
