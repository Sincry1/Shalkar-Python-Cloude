
class Library:
    total_books_in_system = 0 
    def __init__(self, name):
        self.name = name
        self.books = []

    def add_book(self, title):
        self.books.append(title)
        Library.total_books_in_system += 1


if __name__ == "__main__":
    city = Library("Городская")
    school = Library("Школьная")

    city.add_book("Война и мир")
    city.add_book("Мастер и Маргарита")
    school.add_book("Евгений Онегин")

    print(f"В «{city.name}»: {len(city.books)} кн.")
    print(f"В «{school.name}»: {len(school.books)} кн.")
    print("Всего книг в системе:", Library.total_books_in_system)
