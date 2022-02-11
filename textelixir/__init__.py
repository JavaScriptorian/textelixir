import os
from tokenize import group
import pandas
import re
# from pandas.core.algorithms import isin
import spacy
import stanza
# Change to . when exporting
from taggers import stanza_tagger
from taggers import spacy_tagger
from search_results import SearchResults
from ngrams import NGrams
        
class TextElixir:
    def __init__(self, filename=None, lang='en', elixir_filename=None, **kwargs):
        # Parse kwargs
        self.tagger_option = kwargs['tagger_option'] if 'tagger_option' in kwargs else 'stanza:pos'
        self.punct_pos = kwargs['punct_pos'] if 'punct_pos' in kwargs else ['SYM', 'PUNCT']
        self.verbose = kwargs['verbose'] if 'verbose' in kwargs else True
        # Parse args
        self.filename = filename
        self.lang = lang

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
        if 'spacy' in self.tagger_option:
            try:
                if 'accurate' in self.tagger_option:
                    return spacy.load("en_core_web_trf")
                elif 'efficient' in self.tagger_option:
                    return spacy.load("en_core_web_sm")
            except OSError:
                raise Exception('You need to download the training model for SpaCy before you can use it.\nTo do this, type in "python -m spacy download en_core_web_sm" for efficient model or "python -m spacy download en_core_web_trf" for accurate model.')
        elif 'stanza' in self.tagger_option:
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
                if idx % 10 == 0:
                    print(f'\rTagging Lines of Text: {idx}', end='')
                # Get the text of the line.
                if self.extension == 'TXT':
                    line = data[idx]
                elif self.extension in ['TSV', 'GLOB-TXT']:
                    df_line = data.iloc[idx]
                    line = df_line['text']

                line = self.clean_text(line)
                ### SKIP ANY LINES THAT HAVE NO CONTENT ###
                if line == '':
                    continue
                line_index += 1

                if 'stanza' in self.tagger_option:
                    line_index, sentence_index, line_data = stanza_tagger(tagger, line, line_index, sentence_index, tagger_option=self.tagger_option)
                elif 'spacy' in self.tagger_option:
                    line_index, sentence_index, line_data = spacy_tagger(tagger, line, line_index, sentence_index, tagger_option=self.tagger_option)
                

                ### OUTPUT WORD DATA ###
                for w in line_data:
                    if self.extension == 'TXT':
                        output_string = f'{w["line_index"]}\t{w["sentence_index"]}\t{w["word_index"]}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'TSV':
                        tsv_attributes = "\t".join([self.clean_text(df_line[header]) for header in headers])
                        output_string = f'{tsv_attributes}\t{w["sentence_index"]}\t{w["word_index"]}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'GLOB-TXT':
                        output_string = f'{df_line["text_file"]}\t{w["sentence_index"]}\t{w["word_index"]}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                
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
        self.chunk_num = 0
        for chunk in self.elixir:
            self.chunk_num += 1
            normal_words = chunk[chunk['pos'] != 'PUNCT']
            self.word_count += normal_words.shape[0]
        if self.verbose:
            print(f'{self.word_count} words have been loaded!')

    def search(self, search_string, **kwargs):
        # Parse kwargs
        text_filter = kwargs['text_filter'] if 'text_filter' in kwargs else None
        verbose = kwargs['verbose'] if 'verbose' in kwargs else None
        return SearchResults(self.filename, search_string, self.word_count, punct_pos=self.punct_pos, verbose=verbose, text_filter=text_filter)

    def ngrams(self, size, **kwargs):
        return NGrams(self.filename, 
                      size, 
                      group_by=kwargs['group_by'] if 'group_by' in kwargs else 'lower', 
                      sep=kwargs['sep'] if 'sep' in kwargs else ' ', 
                      text_filter=kwargs['text_filter'] if 'text_filter' in kwargs else None, 
                      punct_pos=self.punct_pos, 
                      chunk_num=self.chunk_num)


### Features
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


elixir = TextElixir('Project Gutenberg.elix', verbose=True, tagger_option='spacy:efficient:pos')
import time
t0 = time.time()
ngrams = elixir.ngrams(5)
t1 = time.time()
total = t1-t0
print(total)
# results = elixir.search('have been observed')
# collocates = results.collocates(before=5, after=5, group_by='lemma_pos')


# ibrk = 0

# with open('1grams.txt', 'r', encoding='utf-8') as file_in:
#     words = [i.upper() for i in file_in.read().splitlines()]

# for word in words:
#     # ngrams = elixir.ngrams(5, group_by='lower', bounds=None, sep=' ')
#     # results = elixir.search(f'{word}_VERB', text_filter={'cat': 'PHIL'})
#     # Get all ngrams from philosophy

#     # Book 1 NGrams (Philosophy)
#     ngrams1 = elixir.ngrams(5, group_by='lower', text_filter={'cat': 'PHIL'})
#     # Book 2 NGrams (Not Philosophy)
#     ngrams2 = elixir.ngrams(5, group_by='lower', text_filter={'cat': '!PHIL'})
    
#     # DIVISION BUAHAHAAHA
#     keywords1 = ngrams1 / ngrams2
#     keywords2 = ngrams2 / ngrams1

    
#     ibrk = 0
#     # Get 5 words before and after a search query occurrence.
#     # kwic = results.kwic_lines(before=7, after=7, group_by='text')
#     # # Export as a webpage
#     # kwic.export_as_html(f'verbs/{word}.html', group_by='text')

#     # sentences = results.sentences()
#     # with open(f'sentences/{word}.txt', 'w', encoding='utf-8') as file_out:
#     #     for sent in sentences.sentences:
#     #         print(sent['cit'], sent['sent'], sep='\t', file=file_out)
#     # ibrk = 0

#     # collocates = results.collocates(before=5, after=5)
#     # collocates.export_as_tsv(f'collocates/{word}.tsv')
#     ibrk = 0




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
# TODO: Look into only using a part of stanza that is needed for pos and lemmatization.

# WordCruncher can tokenize text by word.
# WordCruncher does not has an easy-to-type search bar.
# WordCruncher cannot tag a word by lemma or POS.
# WordCruncher cannot tokenize text by sentence.
