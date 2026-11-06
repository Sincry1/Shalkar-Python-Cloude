#1-2
class Person:
    def __init__(self, name, age ):
        self.name = name
        self.age = age

    def introduce(self):
        print(f"Меня зовут {self.name}, мне {self.age} лет")

user=Person("Шалкар", 25)
user.introduce()