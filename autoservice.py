from abc import ABC, abstractmethod


class Part:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __str__(self):
        return f"{self.name} — {self.price} тг"


class Car:
    def __init__(self, number, model, owner):
        self.number = number.upper()
        self.model = model
        self.owner = owner

    def __str__(self):
        return f"{self.model} ({self.number}), владелец: {self.owner}"


class Warehouse:
    def __init__(self):
        self.parts = {
            "масло": Part("Моторное масло", 3000),
            "фильтр": Part("Масляный фильтр", 2500),
            "колодки": Part("Тормозные колодки", 12000)
        }
        self.stock = {"масло": 10, "фильтр": 5, "колодки": 4}

    def show(self):
        for key, part in self.parts.items():
            print(f"{key}: {part}, остаток: {self.stock[key]}")

    def take(self, key, quantity=1):
        if key not in self.parts:
            raise ValueError("Такой детали нет на складе")
        if self.stock[key] < quantity:
            raise ValueError("Недостаточно деталей на складе")
        self.stock[key] -= quantity
        return self.parts[key].price * quantity


class Employee(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def repair(self):
        pass


class Mechanic(Employee):
    def __init__(self, name, specialization):
        super().__init__(name)
        self.specialization = specialization

    def repair(self):
        return f"{self.name} выполняет работу: {self.specialization}"


class EngineMechanic(Mechanic):
    def __init__(self, name):
        super().__init__(name, "ремонт двигателя")


class ChassisMechanic(Mechanic):
    def __init__(self, name):
        super().__init__(name, "ремонт ходовой")


class Invoice:
    def __init__(self, work_price, parts_price):
        self.work_price = work_price
        self.parts_price = parts_price

    @property
    def total(self):
        return self.work_price + self.parts_price

    def __str__(self):
        return f"Работа: {self.work_price} тг; детали: {self.parts_price} тг; итого: {self.total} тг"


class RepairOrder:
    def __init__(self, car, work, mechanic, part_key, quantity, work_price):
        self.car = car
        self.work = work
        self.mechanic = mechanic
        self.part_key = part_key
        self.quantity = quantity
        self.work_price = work_price
        self.invoice = None
        self.completed = False

    def complete(self, warehouse):
        if self.completed:
            raise ValueError("Заказ уже выполнен")
        parts_price = warehouse.take(self.part_key, self.quantity)
        self.invoice = Invoice(self.work_price, parts_price)
        self.completed = True
        return self.invoice

    def __str__(self):
        status = "выполнен" if self.completed else "в работе"
        return f"{self.car} | {self.work} | мастер: {self.mechanic.name} | {status}"


class Garage:
    def __init__(self):
        self.warehouse = Warehouse()
        self.cars = {}
        self.mechanics = [EngineMechanic("Ержан"), ChassisMechanic("Данияр")]
        self.orders = []

    def add_car(self, car):
        if car.number in self.cars:
            raise ValueError("Автомобиль с таким номером уже зарегистрирован")
        self.cars[car.number] = car

    def create_order(self, number, work):
        if number not in self.cars:
            raise ValueError("Автомобиль не найден")
        works = {
            "масло": ("Замена масла", "масло", 4, 5000, EngineMechanic),
            "фильтр": ("Замена фильтра", "фильтр", 1, 2000, EngineMechanic),
            "колодки": ("Замена колодок", "колодки", 1, 6000, ChassisMechanic)
        }
        if work not in works:
            raise ValueError("Неизвестная работа")
        title, part, qty, price, mechanic_type = works[work]
        mechanic = next((m for m in self.mechanics if isinstance(m, mechanic_type)), None)
        if mechanic is None:
            raise ValueError("Нет подходящего механика")
        order = RepairOrder(self.cars[number], title, mechanic, part, qty, price)
        self.orders.append(order)
        return order

    def finish_order(self, index):
        if index < 1 or index > len(self.orders):
            raise ValueError("Заказ не найден")
        return self.orders[index - 1].complete(self.warehouse)


class Console:
    def __init__(self):
        self.garage = Garage()

    def help(self):
        print("""
Команды:
  car НОМЕР МОДЕЛЬ ВЛАДЕЛЕЦ — добавить автомобиль
  stock — показать склад
  order НОМЕР РАБОТА — создать заказ (масло, фильтр, колодки)
  finish НОМЕР — завершить заказ
  orders — показать заказы
  help — помощь
  exit — выход
""")

    def run(self):
        self.help()
        while True:
            command = input("Автосервис> ").strip().split()
            if not command:
                continue
            try:
                action = command[0].lower()
                if action == "exit":
                    break
                elif action == "help":
                    self.help()
                elif action == "stock":
                    self.garage.warehouse.show()
                elif action == "car" and len(command) >= 4:
                    car = Car(command[1], command[2], " ".join(command[3:]))
                    self.garage.add_car(car)
                    print("Автомобиль добавлен")
                elif action == "order" and len(command) == 3:
                    order = self.garage.create_order(command[1].upper(), command[2].lower())
                    print("Создан заказ:", order)
                elif action == "finish" and len(command) == 2:
                    invoice = self.garage.finish_order(int(command[1]))
                    print("Заказ завершён.")
                    print(invoice)
                elif action == "orders":
                    for i, order in enumerate(self.garage.orders, 1):
                        print(f"{i}. {order}")
                else:
                    print("Неизвестная команда или неверные аргументы. Введите help.")
            except (ValueError, IndexError) as error:
                print("Ошибка:", error)


if __name__ == "__main__":
    Console().run()
