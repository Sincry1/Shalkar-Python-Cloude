class Product:
    def __init__(self,price=0):
        self._price = price
    @property
    def price(self):
        return self._price
    
    @price.setter
    def price(self):
        if value < 0:
            raise ValueError(f"цена не может быть ниже 0")
            self.price = value
        else:
            print(f"цена {self.price}")

tovar = Product(1)
print(tovar.price)

tovar = Product(100)
print(tovar.price)
