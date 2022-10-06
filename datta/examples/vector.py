from datta import Data, attribute
from datta._attribute import getter


class Vector(Data):
    x = attribute()  # type: int
    y = attribute()  # type: int
    md = attribute()  # type: int

    @getter(md, dependencies=(x, y))
    def md(self):
        # type: () -> int
        return self.x + self.y
