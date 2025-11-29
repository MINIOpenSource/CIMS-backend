class RGB:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return "RGB({}, {}, {})".format(self.r, self.g, self.b)


class RichText:
    def __init__(
        self,
        text: str,
        font_color: RGB,
        background_color: RGB,
    ):
        self.text = text
        self.font_color = font_color
        self.background_color = background_color

    def __str__(self):
        return self.text


class Sentence:
    def __init__(self):
        self.text = ""
        self.texts = []

    def resolve(self, raw: str):
        for character_index in range(len(raw)):
            if raw[character_index] == "\n":
                pass
