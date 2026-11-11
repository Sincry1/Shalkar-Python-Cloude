class Temperature:
    zero = -273
    def __init__(self , celsius=0):
        self.__celsius = celsius
    @property
    def celsius(self):
        return self.__celsius
    
    @celsius.setter
    def celsius(self):
        if value < self.zero:
            raise ValueError(f"не может быть ниже {self.zero}")
            self.__celsius = value

t = Temperature(20)
print(t.celsius)

t.__celsius = -50
print(t.celsius)

t.__celsius = -300
