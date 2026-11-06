#5
class Rectangle:
    def __init__(self,width,height):
        self.width = width
        self.height = height
    def area(self):
        print(f"area это ", (self.width * self.height))
    def perimeter(self):
        print(f"периметр", 2*(self.width + self.height))
a_b=Rectangle(10,50)
a_b.area()
