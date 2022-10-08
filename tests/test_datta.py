import pytest

from datta import Data, attribute
from datta.examples.json_data import JSONDict


def test_json():
    data = {
        "id": "0001",
        "type": "donut",
        "name": "Cake",
        "ppu": 0.55,
        "batters": {
            "batter": [
                {"id": "1001", "type": "Regular"},
                {"id": "1002", "type": "Strawberry"},
                {"id": "1003", "type": "Blueberry"},
                {"id": "1004", "type": "Devil's Food"},
            ]
        },
        "topping": [
            {"id": "5001", "type": "None"},
            {"id": "5002", "type": "Glazed"},
            {"id": "5005", "type": "Sugar"},
            {"id": "5007", "type": "Powdered Sugar"},
            {"id": "5006", "type": "Chocolate with Sprinkles"},
            {"id": "5003", "type": "Strawberry"},
            {"id": "5004", "type": "Maple"},
        ],
    }
    js = JSONDict(data)
    assert js == JSONDict.deserialize(js.serialize())


def test_circle():
    class Circle(Data):
        PI = attribute(3.14, constant=True)
        radius = attribute()

    assert not Circle.__attributes__["PI"].serialized

    circle = Circle(3)
    assert circle.radius == 3

    assert Circle.deserialize({"radius": 3}) == circle

    with pytest.raises(TypeError):
        Circle(3, PI=300)

    with pytest.raises(TypeError):
        Circle.deserialize({"radius": 3, "PI": 300})


if __name__ == "__main__":
    pytest.main()
