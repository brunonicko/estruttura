from datta import Data, attribute, getter, setter, deleter


class Vector(Data):
    __kwargs__ = {"gen_order": True}

    x = attribute()  # type: int
    y = attribute()  # type: int
    md = attribute()  # type: int

    @getter(md, dependencies=(x, y))
    def _(self):
        # type: () -> int
        return self.x + self.y

    @setter(md)
    def _(self, value):
        # type: (int) -> None
        self.x = self.y = int(value / 2)

    @deleter(md)
    def _(self):
        # type: () -> None
        self.x = self.y = 0
