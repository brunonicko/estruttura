from datta import Data, attribute, getter, setter


class Circle(Data):
    PI = attribute(3.14, constant=True)  # type: float
    radius = attribute(converter=float)  # type: float
    perimeter = attribute()  # type: float

    @getter(perimeter, dependencies=(PI, radius))
    def _(self):
        # type: () -> float
        return 2 * self.PI * self.radius

    @setter(perimeter)
    def _(self, value):
        # type: (float) -> None
        self.radius = value / (2 * self.PI)
