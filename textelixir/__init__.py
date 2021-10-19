import os
import pandas
import re
from pandas.core.algorithms import isin
from pandas.errors import ParserError
import stanza
from .search_results import SearchResults
from .n_grams import NGrams

class TextElixir:
    def __init__(self, filename=None, lang='en', elixir_filename=None, **kwargs):
        if 'elixir_object' in kwargs:
            self.elixir = kwargs['elixir_object']
        # If elixir_filename is not None, don't create an index.
        elif elixir_filename == None:
            self.filename = filename
            self.extension = re.search(r'\.([^\.]+?)$', os.path.basename(filename)).group(1).upper()
            self.basename = re.sub(r'\.[^\.]+?$', r'', os.path.basename(filename))
            self.lang = lang
            self.elixir_filename = f'{self.basename}.elix'
            
            if self.find_indexed_file() == False:
                self.create_indexed_file()
            self.read_elixir()
        else:
            self.elixir_filename = elixir_filename
            self.read_elixir()

        

    # Checks to see if an ELIX file for the project has been created.
    def find_indexed_file(self):
        if os.path.exists(f'{self.basename}.elix'):
            return True
        return False


    def initialize_tagger(self):
        try:
            return stanza.Pipeline(self.lang)
        except:
            stanza.download(self.lang)
            return stanza.Pipeline(self.lang)


    def create_indexed_file(self):
        tagger = self.initialize_tagger()

        
        with open(self.filename, 'r', encoding='utf-8') as file_in:
            if self.extension == 'TXT':
                data = file_in.read().splitlines()
                total_lines = len(data)
            elif self.extension == 'TSV':
                data = pandas.read_csv(file_in, sep='\t', header=0, index_col=None)
                headers = list(data.columns.values)
                index_of_text_column = headers.index('text')
                headers.pop(index_of_text_column)
                total_lines = data.shape[0]
                ibrk = 0
    
        
        line_index = 0
        with open(f'{self.basename}.elix', 'w', encoding='utf-8') as file_out:
            if self.extension == 'TXT':
                print(f'line_index\tsent_index\tword_index\ttext\tlower\tpos\tlemma\tprefix', file=file_out)
            elif self.extension == 'TSV':
                headers_combined = '\t'.join(headers)
                print(f'{headers_combined}\tsent_index\tword_index\ttext\tlower\tpos\tlemma\tprefix', file=file_out)

            for idx in range(0, total_lines):
                if idx % 5 == 0:
                    print(f'\r{idx}/{total_lines-1}', end='')
                # Get the text of the line.
                if self.extension == 'TXT':
                    line = data[idx]
                elif self.extension == 'TSV':
                    df_line = data.iloc[idx]
                    line = df_line['text']

                line = self.clean_text(line)

                lineData = []
                startChars = []
                currentReadIndex = 0
                if line == '':
                    continue

                line_index += 1
                sentence_index = 0
                for sent in tagger(line).sentences:
                    for word in sent.words:
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
                        currentReadIndex = endChar
                    sentence_index += 1
                word_index = 0
                for w in lineData:
                    if self.extension == 'TXT':
                        print(f'{w["line_index"]}\t{w["sentence_index"]}\t{word_index}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}', file=file_out)
                    elif self.extension == 'TSV':
                        tsv_attributes = "\t".join([self.clean_text(df_line[header]) for header in headers])
                        print(f'{tsv_attributes}\t{w["sentence_index"]}\t{word_index}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}', file=file_out)
                    word_index += 1


    def clean_text(self, string):
        string = str(string).replace(u'\xa0', u' ')
        return string


    def read_elixir(self):
        # try:
        with open(self.elixir_filename, 'r', encoding='utf-8') as file_in:
            self.elixir = pandas.read_csv(file_in, sep='\t', index_col=None, header=0, engine='python')
            self.elixir['prefix'].fillna('',inplace=True)
        # except ParserError as err:
        #     # Figure out which line(s) have a problem, since pandas does a poor job at identifying which line has a problem.
        #     expectation = int(re.search(r'Expected (\d+) fields', str(err)).group(1))
            
        #     print('ERROR: Pandas cannot parse your ELIX file. Identifying which lines have problems...')

        #     with open(self.elixir_filename, 'r', encoding='utf-8') as file_in:
        #         for idx, line in enumerate(file_in):
        #             print(f'\r{idx}', end='')
        #             data = line[0:-1].split('\t')

        #             if len(data) != expectation:
        #                 print(f'{idx+1}\t{line}')
        #                 ibrk = 0
        #     print(err)
        #     ibrk = 0
        # except Exception as err:
        #     print(err)
        #     ibrk = 0


    def filter_elixir(self, **kwargs):
        is_already_filtered = False
        for key, value in kwargs.items():
            if is_already_filtered == False:
                if isinstance(value, list):
                    filtered_elixir = self.elixir[self.elixir[key].isin(value)]
                else:
                    filtered_elixir = self.elixir[self.elixir[key] == value]
                is_already_filtered = True
            else:
                if isinstance(value, list):
                    filtered_elixir = filtered_elixir[filtered_elixir[key].isin(value)]
                else:
                    filtered_elixir = filtered_elixir[filtered_elixir[key] == value]
        return TextElixir(elixir_object=filtered_elixir)


    def search(self, search_string, **kwargs):
        return SearchResults(self.elixir, search_string, kwargs)

    def ngrams(self, size, group_by='lower', bounds=None, sep=' '):
        return NGrams(self.elixir, size, group_by, bounds, sep)


