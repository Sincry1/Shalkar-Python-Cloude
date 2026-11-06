
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self._balance = balance  

    def deposit(self, amount):
        if amount <= 0:
            print("Ошибка: сумма пополнения должна быть положительной.")
            return
        self._balance += amount
        print(f"Пополнение на {amount}. Баланс: {self._balance}")

    def withdraw(self, amount):
        if amount <= 0:
            print("Ошибка: сумма снятия должна быть положительной.")
            return
        if amount > self._balance:
            print("Ошибка: недостаточно средств.")
            return
        self._balance -= amount
        print(f"Снятие {amount}. Баланс: {self._balance}")


if __name__ == "__main__":
    acc = BankAccount("Анна", 100)
    acc.deposit(50)
    acc.deposit(-10)
    acc.withdraw(30)
    acc.withdraw(500)
    acc.withdraw(0)
