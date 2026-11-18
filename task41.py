from datetime import date


class Subject:
    Def __init__(self, name):
        self._name = name.strip().capitalize()

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f"Предмет «{self._name}»"


class Person:
    role = "Человек"

    def __init__(self, name):
        self._name = name.strip().title()

    @property
    def name(self):
        return self._name

    def describe(self):
        return f"{self.role}: {self._name}"

    def __str__(self):
        return self.describe()


class Grade:
    def __init__(self, value, subject, teacher):
        self._value = value
        self._subject = subject
        self._teacher = teacher
        self._date = date.today()

    @property
    def value(self):
        return self._value

    @property
    def subject(self):
        return self._subject

    @property
    def teacher(self):
        return self._teacher

    def __str__(self):
        return f"{self._date:%d.%m.%Y} | {self._subject.name}: {self._value} (учитель: {self._teacher.name})"


class Student(Person):
    role = "Ученик"

    def __init__(self, name):
        super().__init__(name)
        self._grades = []

    @property
    def grades(self):
        return list(self._grades)

    def add_grade(self, grade):
        self._grades.append(grade)

    @property
    def average(self):
        if not self._grades:
            return 0.0
        return sum(g.value for g in self._grade) / len(self._grades)

    def subject_averages(self):
        result = {}
        for g in self._grades:
            result.setdefault(g.subject.name, []).append(g.value)
        return {s: sum(v) / len(v) for s, v in result.items()}

    def describe(self):
        return f"{self.role}: {self._name} (оценок: {len(self._grades)}, средний балл: {self.average:.2f})"


class Teacher(Person):
    role = "Учитель"

    def __init__(self, name, subject):
        super().__init__(name)
        self._subject = subject

    @property
    def subject(self):
        return self._subject

    def describe(self):
        return f"{self.role}: {self._name} (предмет: {self._subject.name})"


class SchoolClass:
    def __init__(self, name):
        self._name = name.strip().upper()
        self._students = {}

    @property
    def name(self):
        return self._name

    @property
    def students(self):
        return list(self._students.values())

    def add_student(self, student):
        self._students[student.name.lower()] = student

    def find_student(self, name):
        return self._students[name.strip().lower()]

    @property
    def average(self):
        grades = [g.value for s in self._students.values() for g in s.grades]
        return sum(grades) / len(grades) if grades else 0.0

    def report(self):
        lines = [f"=== Отчёт по классу {self._name} ===",
                 f"Учеников: {len(self._students)}, средний балл класса: {self.average:.2f}", ""]
        ranking = sorted(self._students.values(), key=lambda s: s.average, reverse=True)
        for i, s in enumerate(ranking, 1):
            lines.append(f"{i}. {s}")
            for subj, avg in sorted(s.subject_averages().items()):
                lines.append(f"     - {subj}: {avg:.2f}")
        return "\n".join(lines)

    def __str__(self):
        return f"Класс {self._name} (учеников: {len(self._students)})"


class School:
    HONOR_THRESHOLD = 4.5

    def __init__(self, name):
        self._name = name
        self._classes = {}
        self._subjects = {}
        self._teachers = []

    def __str__(self):
        return (f"Школа «{self._name}»: классов — {len(self._classes)}, "
                f"учителей — {len(self._teachers)}, предметов — {len(self._subjects)}")

    def add_class(self, name):
        school_class = SchoolClass(name)
        self._classes[school_class.name] = school_class
        return school_class

    def get_class(self, name):
        return self._classes[name.strip().upper()]

    def add_subject(self, name):
        subject = Subject(name)
        self._subjects[subject.name.lower()] = subject
        return subject

    def get_subject(self, name):
        return self._subjects[name.strip().lower()]

    def add_teacher(self, name, subject_name):
        teacher = Teacher(name, self.get_subject(subject_name))
        self._teachers.append(teacher)
        return teacher

    def find_teacher(self, subject):
        return [t for t in self._teachers if t.subject is subject][0]

    def add_student(self, class_name, student_name):
        student = Student(student_name)
        self.get_class(class_name).add_student(student)
        return student

    def put_grade(self, class_name, student_name, subject_name, value):
        student = self.get_class(class_name).find_student(student_name)
        subject = self.get_subject(subject_name)
        grade = Grade(value, subject, self.find_teacher(subject))
        student.add_grade(grade)
        return grade

    def honor_students(self, class_name=None):
        classes = [self.get_class(class_name)] if class_name else self._classes.values()
        result = []
        for c in classes:
            for s in c.students:
                if s.grades and s.average >= self.HONOR_THRESHOLD:
                    result.append((c.name, s))
        return sorted(result, key=lambda pair: pair[1].average, reverse=True)

    def overview(self):
        lines = [str(self)]
        lines += [f"  {c}" for c in self._classes.values()]
        lines += [f"  {t}" for t in self._teachers]
        return "\n".join(lines)

    def people(self):
        people = list(self._teachers)
        for c in self._classes.values():
            people += c.students
        return people


def ask(prompt):
    return input(prompt).strip()


def fill_demo_data(school):
    for s in ("Математика", "Физика", "История"):
        school.add_subject(s)
    school.add_teacher("Иванова Мария", "Математика")
    school.add_teacher("Петров Алексей", "Физика")
    school.add_teacher("Сидорова Анна", "История")
    school.add_class("9А")
    for n in ("Ахметов Ержан", "Беков Данияр", "Смирнова Ольга"):
        school.add_student("9А", n)
    data = [("Ахметов Ержан", "Математика", 5), ("Ахметов Ержан", "Физика", 5),
            ("Ахметов Ержан", "История", 4), ("Беков Данияр", "Математика", 3),
            ("Беков Данияр", "Физика", 4), ("Смирнова Ольга", "Математика", 5),
            ("Смирнова Ольга", "История", 5), ("Смирнова Ольга", "Физика", 5)]
    for student, subject, value in data:
        school.put_grade("9А", student, subject, value)


def handle(school, command):
    if command == "info":
        print(school.overview())
    elif command == "add_class":
        print("Создан:", school.add_class(ask("Название класса (например, 9А): ")))
    elif command == "add_student":
        class_name = ask("Класс: ")
        print("Добавлен:", school.add_student(class_name, ask("ФИО ученика: ")))
    elif command == "add_subject":
        print("Добавлен:", school.add_subject(ask("Название предмета: ")))
    elif command == "add_teacher":
        name = ask("ФИО учителя: ")
        print("Добавлен:", school.add_teacher(name, ask("Предмет: ")))
    elif command == "grade":
        class_name = ask("Класс: ")
        student = ask("ФИО ученика: ")
        subject = ask("Предмет: ")
        value = int(ask("Оценка (2-5): "))
        print("Поставлено:", school.put_grade(class_name, student, subject, value))
    elif command == "avg":
        class_name = ask("Класс: ")
        student = school.get_class(class_name).find_student(ask("ФИО ученика: "))
        print(f"Средний балл {student.name}: {student.average:.2f}")
    elif command == "history":
        class_name = ask("Класс: ")
        student = school.get_class(class_name).find_student(ask("ФИО ученика: "))
        for g in student.grades:
            print(" ", g)
    elif command == "report":
        print(school.get_clas(ask("Класс: ")).report())
    elif command == "honors":
        class_name = ask("Класс (Enter — вся школа): ")
        for c, s in school.honor_students(class_name or None):
            print(f"  [{c}] {s}")
    elif command == "people":
        for p in school.people():
            print(" ", p)


school = School("Гимназия №1")
fill_demo_data(school)
print(school)
while True:
    command = ask("\n> ").lower()
    handle(school, command)
