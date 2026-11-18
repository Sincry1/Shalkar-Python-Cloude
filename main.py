from abc import ABC, abstractmethod


class Subject:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f"Предмет {self._name}"


class Person(ABC):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def describe(self):
        pass

    def __str__(self):
        return self.describe()


class Grade:
    def __init__(self, value, subject, teacher):
        self._value = value
        self._subject = subject
        self._teacher = teacher

    @property
    def value(self):
        return self._value

    def __str__(self):
        return f"{self._subject.name}: {self._value} (учитель: {self._teacher.name})"


class Student(Person):
    def __init__(self, name):
        super().__init__(name)
        self._grades = []

    @property
    def grades(self):
        return self._grades

    def add_grade(self, grade):
        self._grades.append(grade)

    @property
    def average(self):
        if len(self._grades) == 0:
            return 0
        total = 0
        for grade in self._grades:
            total += grade.value
        return total / len(self._grades)

    def describe(self):
        return f"Ученик: {self._name}, оценок: {len(self._grades)}, средний балл: {round(self.average, 2)}"


class Teacher(Person):
    def __init__(self, name, subject):
        super().__init__(name)
        self._subject = subject

    @property
    def subject(self):
        return self._subject

    def describe(self):
        return f"Учитель: {self._name}, предмет: {self._subject.name}"


class SchoolClass:
    def __init__(self, name):
        self._name = name.strip().upper()
        self._students = []

    @property
    def name(self):
        return self._name

    @property
    def students(self):
        return self._students

    def add_student(self, student):
        self._students.append(student)

    def find_student(self, name):
        for student in self._students:
            if student.name == name:
                return student

    @property
    def average(self):
        total = 0
        count = 0
        for student in self._students:
            for grade in student.grades:
                total += grade.value
                count += 1
        if count == 0:
            return 0
        return total / count

    def __str__(self):
        return f"Класс {self._name}, учеников: {len(self._students)}"


class School:
    HONOR_THRESHOLD = 4.5

    def __init__(self, name):
        self._name = name
        self._classes = []
        self._subjects = []
        self._teachers = []

    def __str__(self):
        return f"Школа {self._name}: классов {len(self._classes)}, учителей {len(self._teachers)}, предметов {len(self._subjects)}"

    def add_class(self, name):
        school_class = SchoolClass(name)
        self._classes.append(school_class)
        return school_class

    def get_class(self, name):
        for school_class in self._classes:
            if school_class.name == name.strip().upper():
                return school_class

    def add_subject(self, name):
        subject = Subject(name)
        self._subjects.append(subject)
        return subject

    def get_subject(self, name):
        for subject in self._subjects:
            if subject.name.lower() == name.strip().lower():
                return subject

    def add_teacher(self, name, subject_name):
        teacher = Teacher(name, self.get_subject(subject_name))
        self._teachers.append(teacher)
        return teacher

    def find_teacher(self, subject):
        for teacher in self._teachers:
            if teacher.subject.name == subject.name:
                return teacher

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

    def honor_students(self, class_name):
        result = []
        for school_class in self._classes:
            if class_name == "" or school_class.name == class_name.strip().upper():
                for student in school_class.students:
                    if len(student.grades) > 0 and student.average >= self.honor_tgreshhold:
                        result.append(student)
        return result

    def overview(self):
        print(self)
        for school_class in self._classes:
            print(" ", school_class)
        for teacher in self._teachers:
            print(" ", teacher)

    def people(self):
        people = []
        for teacher in self._teachers:
            people.append(teacher)
        for school_class in self._classes:
            for student in school_class.students:
                people.append(student)
        return people


school = School("школа №1")
school.add_subject("Математика")
school.add_subject("Физика")
school.add_subject("История")
school.add_teacher("Иванова Мария", "Математика")
school.add_teacher("Петров Алексей", "Физика")
school.add_teacher("Сидорова Анна", "История")
school.add_class("9А")
school.add_student("9А", "Ахметов Ержан")
school.add_student("9А", "Беков Данияр")
school.add_student("9А", "Смирнова Ольга")
school.put_grade("9А", "Ахметов Ержан", "Математика", 5)
school.put_grade("9А", "Ахметов Ержан", "Физика", 5)
school.put_grade("9А", "Ахметов Ержан", "История", 4)
school.put_grade("9А", "Беков Данияр", "Математика", 3)
school.put_grade("9А", "Беков Данияр", "Физика", 4)
school.put_grade("9А", "Смирнова Ольга", "Математика", 5)
school.put_grade("9А", "Смирнова Ольга", "История", 5)
school.put_grade("9А", "Смирнова Ольга", "Физика", 5)

print(school)

while True:
    command = input("\n> ").
        if command == "grade":

        class_name = input("Класс: ")
        student_name = input("ФИО ученика: ")
        subject_name = input("Предмет: ")
        value = int(input("Оценка (2-5): "))
        print("Поставлено:", school.put_grade(class_name, student_name, subject_name, value))
    elif command == "avg":
        school_class = school.get_class(input("Класс: "))
        student = school_class.find_student(input("ФИО ученика: "))
        print(f"Средний балл {student.name}: {round(student.average, 2)}") 
    elif command == "honors":
        for student in school.honor_students(input("Класс (Enter — вся школа): ")):
            print(" ", student)
    elif command == "people":
        for person in school.people():
            print(" ", person)
    elif command == "help":
        print("Команды:")
        print("  grade   - поставить оценку")
        print("  avg     - средний балл ученика")
        print("  report  - отчёт по классу")
        print("  honors  - список отличников")
        print("  people  - все учителя и ученики")
        print("  help    - список команд")
        print("  exit    - выход")

    elif command == "exit":
        print("До свидания!")
        break
