import pytest

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


if __name__ == "__main__":
    pytest.main()
