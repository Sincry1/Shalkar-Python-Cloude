#7
class Movie:
    def __init__(self,title,genre,rating):
        self.title = title
        self.genre = genre
        self.rating = rating
    def ocenka(self):
        if self.rating >= 7:
            print(self.title)

movies = (
    Movie("Интерстеллар", "Научная фантастика", 8.6),
    Movie("Начало", "Фантастика, Боевик", 8.7),
    Movie("Зеленая миля", "Драма, Фэнтези", 9.1),
    Movie("Бойцовский клуб", "Триллер, Драма", 8.7),
    Movie("Темный рыцарь", "Боевик, Триллер", 8.5)
)
for i in movies:
    i.ocenka()
