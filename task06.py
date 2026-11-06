#6
class Student:
    def __init__(self,name,grades):
        self.name = name
        self.grades = grades
    def average_grade(self):
        print(f"средний балл твой : " , sum(self.grades) / len(self.grades))
temshik=Student("iska", [2,3,4,5,6,7,8,9])
temshik.average_grade()