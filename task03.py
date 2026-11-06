class Book:
    def __init__(self, title, author, pages):
        self.title=title
        self.author=author
        self.pages=pages
    def reading_time(self):
        print(f"ты прочитал {self.pages}, страниц ")
my_book = Book("Капитанская дочка", "Александр Пушкин", 12)
my_book.reading_time()