#8
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius
    def to_fahrenheit(self):
        print(f"целсий теперь",(self.celsius * 9/5 + 32))
gradus = Temperature(100)
gradus.to_fahrenheit()
