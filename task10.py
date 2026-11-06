#10
import math
class Circle:
    def __init__(self,radius):
        self.radius = radius
    def area(self):
        print(math.pi * (self.radius**2))
    def circumference(self):
        print(2 * math.pi * self.radius)
count=Circle(100)
count.area()
count.circumference()
print("WW")