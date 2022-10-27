import copy

import pytest

from estruttura import ImmutableDictStructure, ImmutableListStructure, Relationship


class ImmutableDict(ImmutableDictStructure):
    __slots__ = ("__internal",)

    def __getitem__(self, key):
        return self.__internal[key]

    def _hash(self):
        return hash(tuple(sorted(self.__internal.items(), key=lambda i: i[0])))

    def _eq(self, other):
        return type(self) is type(other) and self.__internal == other.__internal  # noqa

    def __len__(self):
        return len(self.__internal)

    def __iter__(self):
        return iter(self.__internal)

    def _do_init(self, initial_values):
        self.__internal = initial_values

    def _do_clear(self):
        cls = type(self)
        new_self = cls.__new__(cls)
        new_self.__internal = {}
        return new_self

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts):
        new_internal = dict(self.__internal)
        new_internal.update(updates_and_inserts)
        for d in deletes:
            del new_internal[d]
        new_self = copy.copy(self)
        new_self.__internal = new_internal
        return new_self

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self.__internal = values
        return self

    def get(self, key, fallback=None):
        return self.__internal.get(key, fallback)


class ImmutableList(ImmutableListStructure):
    __slots__ = ("__internal",)

    def __getitem__(self, item):
        return self.__internal[item]

    def _do_init(self, initial_values):
        self.__internal = list(initial_values)

    def _do_insert(self, index, new_values):
        new_internal = list(self.__internal)
        new_internal[index:index] = new_values

        new_self = copy.copy(self)
        new_self.__internal = new_internal
        return new_self

    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        new_internal = list(self.__internal)
        del new_internal[index:stop]
        new_internal[post_index:post_index] = values

        new_self = copy.copy(self)
        new_self.__internal = new_internal
        return new_self

    def _do_delete(self, index, stop, old_values):
        new_internal = list(self.__internal)
        del new_internal[index:stop]

        new_self = copy.copy(self)
        new_self.__internal = new_internal
        return new_self

    def _do_update(self, index, stop, old_values, new_values):
        new_internal = list(self.__internal)
        new_internal[index:stop] = new_values

        new_self = copy.copy(self)
        new_self.__internal = new_internal
        return new_self

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self.__internal = list(values)
        return self

    def count(self, value):
        return len(self.__internal)

    def index(self, value, start=None, stop=None):
        return self.__internal.index(value, start, stop)

    def _do_clear(self):
        new_self = copy.copy(self)
        new_self.__internal = []
        return new_self

    def _hash(self):
        return hash(tuple(self.__internal))

    def _eq(self, other):
        return type(self) is type(other) and self.__internal == other.__internal  # noqa

    def __len__(self):
        return len(self.__internal)


json_relationship = Relationship(
    types=(str, int, bool, float, None, "JSONDict", "JSONList"), extra_paths=(__name__,)
)  # type: Relationship[str | int | bool | float | None | JSONDict | JSONList]


class JSONList(ImmutableList):
    relationship = json_relationship


class JSONDict(ImmutableDict):
    key_relationship = Relationship(types=(str,))  # type: Relationship[str]
    relationship = json_relationship


def test_json():
    example = {
        "glossary": {
            "__class__": "foo",
            "__state__": "bar",
            "title": "example glossary",
            "GlossDiv": {
                "title": "S",
                "GlossList": {
                    "GlossEntry": {
                        "ID": "SGML",
                        "SortAs": "SGML",
                        "GlossTerm": "Standard Generalized Markup Language",
                        "Acronym": "SGML",
                        "Abbrev": "ISO 8879:1986",
                        "GlossDef": {
                            "para": "A meta-markup language, used to create markup languages such as DocBook.",
                            "GlossSeeAlso": ["GML", "XML"],
                        },
                        "GlossSee": "markup",
                    }
                },
            },
        },
    }
    data = JSONDict.deserialize(example)
    assert data.serialize() == example

    assert isinstance(data["glossary"], JSONDict)
    assert isinstance(data["glossary"]["GlossDiv"]["GlossList"]["GlossEntry"]["GlossDef"]["GlossSeeAlso"], JSONList)


if __name__ == "__main__":
    pytest.main()
