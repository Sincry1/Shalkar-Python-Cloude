class Age:
    min_age = 0
    max_age = 120
    def __init__(self, age):
        self.age = age
    @property
    def age(self):
        return self.__age
    @age.setter
    def age(self,value):
        if not 0 <= value <= 120:
            raise ValueError("0 or 120")
        self.__age = value

god = Age(120)
print(god.age)
