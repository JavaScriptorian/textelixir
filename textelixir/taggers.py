import re
import stanza

def stanza_tagger(tagger, line, line_index, sentence_index, tagger_option='stanza:pos', **kwargs):
    # Parse kwargs
    line_data = [] 
    start_chars= []
    current_read_index = 0
    for j, sent in enumerate(tagger(line).sentences):
        sentence_index += 1
        word_index = 1
        for q, word in enumerate(sent.words):
            # Get the start char and end char of the string.
            characterSearch = re.search(
                r'start_char=(\d+?)\|end_char=(\d+?)$', word.parent.misc)
            start_char = int(characterSearch.group(1))
            if start_char not in start_chars:
                start_chars.append(start_char)
                duplicate = False
            else:
                duplicate = True
            end_char = int(characterSearch.group(2))

            actual_text = line[start_char:end_char]
            pos = word.xpos if ':xpos' in tagger_option else word.pos
            # Label punctuation accordingly.
            if word.pos in ['SYM', 'PUNCT']:
                pos = 'PUNCT'
            lemma = word.lemma
            if lemma == None:
                lemma = actual_text.upper()

            # If there are underscores in the lemma or actual_text, then it needs to be escaped.
            actual_text = re.sub(r'(?<!\\\\)_', r'\\\\_', actual_text)
            lemma = re.sub(r'(?<!\\\\)_', r'\\\\_', actual_text)

            if duplicate:
                line_data[-1]['pos2'] = pos
                line_data[-1]['lemma2'] = lemma
            else:
                line_data.append({
                    'text': actual_text,
                    'pos': pos,
                    'lemma': lemma.upper(),
                    'prefix_text': line[current_read_index:start_char],
                    'line_index': line_index,
                    'sentence_index': sentence_index,
                    'word_index': word_index
                })
                # If it's the first word and first sentence in a line, add 3 spaces (for KWIC purposes)
                if j == 0 and q == 0:
                    if line_data[-1]['prefix_text'] == '':
                        line_data[-1]['prefix_text'] == '   '
            current_read_index = end_char
            word_index += 1
        
    return (line_index, sentence_index, line_data)


def spacy_tagger(tagger, line, line_index, sentence_index, tagger_option='spacy:pos', **kwargs):
    # Parse kwargs
    line_data = [] 
    start_chars= []
    current_read_index = 0
    start_char = 0
    sentences = tagger(line)
    word_index = 1
    for j, word in enumerate(sentences):
        if word.is_sent_start:
            sentence_index += 1
            word_index = 1
        # Get the start char and end char of the string.
        start_char = line.index(word.text, start_char)
        if start_char not in start_chars:
            start_chars.append(start_char)
            duplicate = False
        else:
            duplicate = True
        end_char = start_char + len(word.text)
        actual_text = line[start_char:end_char]



        pos = word.tag_ if ':xpos' in tagger_option else word.pos_
        # Label punctuation accordingly.
        if word.pos_ in ['SYM', 'PUNCT']:
            pos = 'PUNCT'
        lemma = word.lemma_
        if lemma == None:
            lemma = actual_text.upper()

        # If there are underscores in the lemma or actual_text, then it needs to be escaped.
        actual_text = re.sub(r'(?<!\\\\)_', r'\\\\_', actual_text)
        lemma = re.sub(r'(?<!\\\\)_', r'\\\\_', lemma)
        if duplicate:
            line_data[-1]['pos2'] = pos
            line_data[-1]['lemma2'] = lemma
        else:
            line_data.append({
                'text': actual_text,
                'pos': pos,
                'lemma': lemma.upper(),
                'prefix_text': line[current_read_index:start_char],
                'line_index': line_index,
                'sentence_index': sentence_index,
                'word_index': word_index
            })
            # If it's the first word and first sentence in a line, add 3 spaces (for KWIC purposes)
            if j == 0:
                if line_data[-1]['prefix_text'] == '':
                    line_data[-1]['prefix_text'] == '   '
            if word_index == 1:
                line_data[-1]['prefix_text'] = ' '
        current_read_index = end_char
        # Make start_char into end_char, for the next word
        start_char = end_char
        word_index += 1
    return (line_index, sentence_index, line_data)