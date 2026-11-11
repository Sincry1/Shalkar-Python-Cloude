class Playlist:
    def __init__(self, name,):
        self.name = name 
        self._songs = []
    def add_song(self,song):
        if song in self._songs:
            print(f"{song} уже есть в листе")
            return
        self._songs.append(song)
        print(f'added:{song}')
    def remove_song(self,song):
        if song not in self._songs:
            print(f'{song} netu')
            return
        self._songs.remove(song)
        print(f'deleted: {song}')
    @property
    def song(self):
        return list(self._songs)
p = Playlist("favourite")
p.add_song("firestarter")
p.add_song("know my name")
p.remove_song("firestarter")

print(p.song)