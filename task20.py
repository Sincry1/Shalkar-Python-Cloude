class User:
    def __init__(self, username , password):
        self.username = username
        self.__password = password
    def checkpassword(self ,password):
        if self.__password == password:
            print("ваш пароль верный")
        else:
            print("неверно")
user = User("Sincry","Password123")
print(user.checkpassword("Password123"))
