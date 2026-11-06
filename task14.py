
class BankAccount:
    total_accounts = 0 

    def __init__(self, owner):
        BankAccount.total_accounts += 1
        self.owner = owner
        self.account_number = BankAccount.total_accounts

    def __str__(self):
        return f"Счёт №{self.account_number}, владелец: {self.owner}"


if __name__ == "__main__":
    a = BankAccount("Анна")
    b = BankAccount("Борис")
    c = BankAccount("Виктор")

    for acc in (a, b, c):
        print(acc)
    print("Всего счетов в банке:", BankAccount.total_accounts)
