class Employee:
    total_employees = 0
    def __init__(self, name, position):
        self.name = name
        self.position = position
        Employee.total_employees += 1

print(Employee.total_employees)
emp1 = Employee("Алексей", "Разработчик")
emp2 = Employee("Мария", "Дизайнер")
print(Employee.total_employees)  
