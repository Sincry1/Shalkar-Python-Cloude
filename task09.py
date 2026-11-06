#9
class ShoppingItem:
    def __init__(self, name, price, quantity):
        self.name = name 
        self.price = price
        self.quantity = quantity
    def total_cost(self):\
    print(f'total cost',(self.price*self.quantity))

tovar=ShoppingItem("gorilla",500,10)
tovar.total_cost()
