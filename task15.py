
class Product:
    vat_rate = 0.2  

    def __init__(self, name):
        self.name = name

    def price_with_vat(self, price):
        return price * (1 + self.vat_rate)


if __name__ == "__main__":
    milk = Product("Молоко")
    print(f"{milk.name}: 100 -> {milk.price_with_vat(100):.2f} с НДС")
    Product.vat_rate = 0.12
    bread = Product("Хлеб")
    print(f"{bread.name}: 100 -> {bread.price_with_vat(100):.2f} с НДС (ставка 12%)")
