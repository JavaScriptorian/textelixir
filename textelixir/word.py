class Word:
    def __init__(self, word, pos, lemma):
        self.word = word
        self.pos = pos
        self.lemma = lemma
        self.lower = word.lower()