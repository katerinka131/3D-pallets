class Box:
    def __init__(self, id, d1, d2, d3):
        self.id = id
        self.d1, self.d2, self.d3 = d1, d2, d3

    def volume(self):
        return self.d1 * self.d2 * self.d3

    def get_orientations(self):
        return [
            (self.d1, self.d2, self.d3),
            (self.d2, self.d1, self.d3)
        ]