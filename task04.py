#4
class car:
    def __init__(self, brand, model, year):
        self.brand = brand
        self.model = model
        self.year = year
    def get_age(self):
        print(f"твоя машинка {self.year} года ")
my_car = car("toyota","ZXC", 2001)
my_car.get_age()