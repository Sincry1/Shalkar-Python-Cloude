
class Order:
    orders_count = 0  # атрибут класса

    def __init__(self, item):
        self.item = item
        Order.orders_count += 1

    @classmethod
    def get_total_orders(cls):
        return cls.orders_count


if __name__ == "__main__":
    print("Заказов до создания:", Order.get_total_orders())
    Order("Ноутбук")
    Order("Мышь")
    Order("Клавиатура")
    print("Заказов после создания:", Order.get_total_orders())
