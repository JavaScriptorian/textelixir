import os
import pandas
import re
from pandas.core.algorithms import isin
from pandas.errors import ParserError
import stanza
# Change to . when exporting
from search_results import SearchResults
from n_grams import NGrams
        
class TextElixir:
    def __init__(self, filename=None, lang='en', elixir_filename=None, **kwargs):
        self.filename = filename
        self.lang = lang
        self.punct_pos = ['SYM', 'PUNCT']
        # Set verbose argument.
        if 'verbose' in kwargs:
            self.verbose = kwargs['verbose']
        else:
            self.verbose = False

        # Check for pre-loaded ELIX file.
        if isinstance(self.filename, str) and self.filename.endswith('elix'):
            self.read_elixir()
        else:
            # Check to see if the filename is a list, e.g. glob
            if isinstance(filename, list):
                self.filename = filename
                self.extension = 'GLOB-' + re.search(r'\.([^\.]+?)$', os.path.basename(filename[0])).group(1).upper()
                self.basename = 'Glob Elixir'
                self.elixir_filename = f'{self.basename}.elix'
            else:
                self.extension = re.search(r'\.([^\.]+?)$', os.path.basename(filename)).group(1).upper()
                self.basename = re.sub(r'\.[^\.]+?$', r'', os.path.basename(filename))
                self.elixir_filename = f'{self.basename}.elix'
            if self.find_indexed_file() == False:
                self.create_indexed_file()
            self.filename = self.elixir_filename
            self.read_elixir()

    def initialize_tagger(self):
        try:
            return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=True)
        except:
            stanza.download(self.lang)
            return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=False)
        

    def find_indexed_file(self):
        if os.path.exists(f'{self.basename}.elix'):
            return True
        return False

    def create_indexed_file(self):
        if self.extension == 'TXT':
            with open(self.filename, 'r', encoding='utf-8') as file_in:
                data = file_in.read().splitlines()
                total_lines = len(data)
        elif self.extension == 'TSV':
            with open(self.filename, 'r', encoding='utf-8') as file_in:
                data = pandas.read_csv(file_in, sep='\t', header=0, index_col=None)
                headers = list(data.columns.values)
                index_of_text_column = headers.index('text')
                headers.pop(index_of_text_column)
                total_lines = data.shape[0]
        # Convert a GLOB-TXT into a TSV with two columns: text_file and text.
        elif self.extension == 'GLOB-TXT':
            filenames = []
            lines = []
            for f in self.filename:
                fBasename = os.path.basename(f)
                with open(f, 'r', encoding='utf-8') as file_in:
                    for line in file_in.read().splitlines():
                        filenames.append(fBasename)
                        lines.append(line)
            zipped = list(zip(filenames, lines))
            headers = ['text_file', 'text']
            data = pandas.DataFrame(zipped, columns=headers)
            index_of_text_column = 1
            total_lines = data.shape[0]
            
        tagger = self.initialize_tagger()

        line_index = 0
        words_tagged = 0
        with open(f'{self.basename}.elix', 'w', encoding='utf-8') as file_out:
            ### PRINT HEADERS FOR ELIX FILE ###
            if self.extension in ['TXT']:
                print(f'line_index\tsent_index\tword_index\ttext\tlower\tpos\tlemma\tprefix', file=file_out)
            elif self.extension == 'TSV':
                headers_combined = '\t'.join(headers)
                print(f'{headers_combined}\tsent_index\tword_index\ttext\tlower\tpos\tlemma\tprefix', file=file_out)
            elif self.extension == 'GLOB-TXT':
                print(f'text_file\tsent_index\tword_index\ttext\tlower\tpos\tlemma\tprefix', file=file_out)


            sentence_index = 0
            ### GET CURRENT LINE TO TAG ###
            for idx in range(0, total_lines):
                # Get the text of the line.
                if self.extension == 'TXT':
                    line = data[idx]
                elif self.extension in ['TSV', 'GLOB-TXT']:
                    df_line = data.iloc[idx]
                    line = df_line['text']

                line = self.clean_text(line)

                lineData = []
                startChars = []
                currentReadIndex = 0

                ### SKIP ANY LINES THAT HAVE NO CONTENT ###
                if line == '':
                    continue

                line_index += 1
                for j, sent in enumerate(tagger(line).sentences):
                    for q, word in enumerate(sent.words):
                        characterSearch = re.search(
                            r'start_char=(\d+?)\|end_char=(\d+?)$', word.parent.misc)
                        startChar = int(characterSearch.group(1))
                        if startChar not in startChars:
                            startChars.append(startChar)
                            duplicate = False
                        else:
                            duplicate = True

                        endChar = int(characterSearch.group(2))

                        actualText = line[startChar:endChar]
                        pos = word.pos

                        lemma = word.lemma
                        if lemma == None:
                            lemma = actualText.upper()

                        # If there are underscores in the lemma or actualText, then it needs to be escaped.
                        actualText = re.sub(r'(?<!\\\\)_', r'\\\\_', actualText)
                        lemma = re.sub(r'(?<!\\\\)_', r'\\\\_', actualText)

                        if duplicate:
                            lineData[-1]['pos2'] = pos
                            lineData[-1]['lemma2'] = lemma
                        else:
                            lineData.append({
                                'text': actualText,
                                'pos': pos,
                                'lemma': lemma.upper(),
                                'prefix_text': line[currentReadIndex:startChar],
                                'line_index': line_index,
                                'sentence_index': sentence_index
                            })
                            # If it's the first word and first sentence in a line, add 3 spaces (for KWIC purposes)
                            if j == 0 and q == 0:
                                if lineData[-1]['prefix_text'] == '':
                                    lineData[-1]['prefix_text'] == '   '
                                ibrk = 0
                            words_tagged += 1
                            if words_tagged % 100 == 0:
                                print(f'\rWords Tagged: {words_tagged}', end='')
                        currentReadIndex = endChar
                    sentence_index += 1

                ### OUTPUT WORD DATA ###
                word_index = 0
                for w in lineData:
                    if self.extension == 'TXT':
                        output_string = f'{w["line_index"]}\t{w["sentence_index"]}\t{word_index}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'TSV':
                        tsv_attributes = "\t".join([self.clean_text(df_line[header]) for header in headers])
                        output_string = f'{tsv_attributes}\t{w["sentence_index"]}\t{word_index}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'GLOB-TXT':
                        output_string = f'{df_line["text_file"]}\t{w["sentence_index"]}\t{word_index}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    word_index += 1
                
                    output_string = re.sub(r'(?<!\\)"', r'\\"', output_string)
                    print(output_string, file=file_out)



    def clean_text(self, string):
        string = str(string).replace(u'\xa0', u' ')
        return string


    def read_elixir(self):
        if self.verbose:
            print(f'Reading {self.filename}...')
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        self.word_count = 0
        chunk_num = 0
        for chunk in self.elixir:
            chunk_num += 1
            normal_words = chunk[chunk['pos'] != 'PUNCT']
            self.word_count += normal_words.shape[0]
        if self.verbose:
            print(f'{self.word_count} words have been loaded!')

    def search(self, search_string, **kwargs):
        if 'verbose' in kwargs:
            return SearchResults(self.filename, search_string, self.word_count, punct_pos=self.punct_pos, verbose=kwargs['verbose'])
        else:
            return SearchResults(self.filename, search_string, self.word_count, punct_pos=self.punct_pos)

    def ngrams(self, size, group_by='lower', bounds=None, sep=' '):
        return NGrams(self.elixir, size, group_by, bounds, sep)


# Make KWIC lines work based on new tuples for results indices
# Double-check that your numbers are correct for MI. It seems to be a little off.

### Features
#! TODO: Tagger needs work. It hasn't been touched in ages, and it is very convoluted.
#! TODO: Develop NGram List
# TODO: Make KWIC Lines work based on new tuples for results indices.
# TODO: Keep stopwords for common languages to remove in collocates?
# TODO: Calculate TTR.
# TODO: Develop Moving Average Type-To-Token Ratio.
#! TODO: Frequency By Section and 10ths.
# TODO: Search for multiple pos at once. /NOUN|PROPN/
# TODO: Search for *.
# TODO: Search for ?.


### Optimization
#! TODO: Check for errors when dealing with 3+ words. Do the correct block numbers get output?
# TODO: Optimize SearchResults.get_previous_words() by returning early if the word is the current search word.
# TODO: Improve tagging feature to allow some options like ignore_pos, ignore_lemma. Add spacy tagger option
# TODO: Look into only using a part of stanza that is needed for pos and lemmatization.
# TODO: Make all curly quotes into straight quotes?

### Visualizations
# TODO: Create CSV/TSV export for KWIC Lines
# TODO: Create JSON export for KWIC lines
# TODO: Create HTML export for KWIC lines
# TODO: Create CSV/TSV/TXT export for n-gram frequency 

# TODO: Add headers to the top of KWIC HTML table
# TODO: Copy all button
# TODO: Copy row buttons
# TODO: Sort table by column
# TODO: Change column to POS/TEXT/LOWER/LEMMA

# Tag a corpus by part of speech and lemma.
elixir = TextElixir('Bethany_Grey_Corpus.elix')
# Get a SearchResults object that can then get kwic lines, collocates, and sentences.

with open('1grams.txt', 'r', encoding='utf-8') as file_in:
    words = [i.upper() for i in file_in.read().splitlines()]

for word in words:
    results = elixir.search(f'{word}_VERB')
    # Get 5 words before and after a search query occurrence.
    kwic = results.kwic_lines(before=7, after=7, group_by='text')
    # Export as a webpage
    kwic.export_as_html(f'verbs/{word}.html', group_by='text')

    sentences = results.sentences()
    with open(f'sentences/{word}.txt', 'w', encoding='utf-8') as file_out:
        for sent in sentences.sentence_lines:
            print(sent, file=file_out)

    # collocates = results.collocates(before=5, after=5)
    # collocates.export_as_tsv(f'collocates/{word}.tsv')
    ibrk = 0


# Get strongest collocates of a search query occurrence.
# collocates = results.collocates(before=5, after=5, group_by='lemma')
# Output strongest collocates to an HTML table.
# collocates.export_as_html('test.html')
# Perform collocates
# collocates = results.find_collocates(before=0, after=5, group_by='lower_pos', mi_threshold=4, sample_size_threshold=2)
# for friend in collocates.friends:
#     print(friend)


### Done
# Make it possible to see collocate friends to left and right.
# Handle collocate duplicates. Example: ETS occurs 2 times, and TEST occurs 3 times in a 5-word radius.
# Double-check that the numbers for MI are correct. Still getting a lot of stopwords in it.
# Search for a specific pos on a word/lemma
# Export TXT of collocates
# Rewrite glob-txt code.

# WordCruncher can tokenize text by word.
# WordCruncher does not has an easy-to-type search bar.
# WordCruncher cannot tag a word by lemma or POS.
# WordCruncher cannot tokenize text by sentence.