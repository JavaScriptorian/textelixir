import csv
import json
import os
from pkg_resources import resource_filename
import pandas
import re
from .taggers import stanza_tagger
from .taggers import spacy_tagger
from .search_results import SearchResults
from .ngrams import NGrams
from .tables import spacy_taggers
        
class TextElixir:
    def __init__(self, filename=None, lang='en', elixir_filename=None, **kwargs):
        # Parse kwargs
        self.tagger_option = kwargs['tagger_option'] if 'tagger_option' in kwargs else 'stanza:pos'
        self.punct_pos = kwargs['punct_pos'] if 'punct_pos' in kwargs else ['SYM', 'PUNCT', 'SPACE']
        self.verbose = kwargs['verbose'] if 'verbose' in kwargs else True
        # Parse args
        self.filename = filename
        self.lang = lang

        # Check for pre-loaded ELIX file.
        # TODO: This will be broken when I change it to a folder.
        if isinstance(self.filename, str) and os.path.exists(f'{self.filename}/corpus.elix'):
            self.filename = f'{self.filename}/corpus.elix'
            self.read_elixir()
        else:
            # Check to see if the filename is a list, e.g. glob
            if isinstance(filename, list):
                self.filename = filename
                self.extension = 'GLOB-' + re.search(r'\.([^\.]+?)$', os.path.basename(filename[0])).group(1).upper()
                self.basename = 'Glob Elixir'
                self.elixir_filename = f'{self.basename}/corpus.elix'
            else:
                self.extension = re.search(r'\.([^\.]+?)$', os.path.basename(filename)).group(1).upper()
                self.basename = re.sub(r'\.[^\.]+?$', r'', os.path.basename(filename))
                self.elixir_filename = f'{self.basename}/corpus.elix'
            if self.find_indexed_file() == False:
                self.create_indexed_file()
                self.create_word_list()
            self.filename = self.elixir_filename
            self.read_elixir()

    def initialize_tagger(self):
        if 'spacy' in self.tagger_option:
            # Access tagger table
            tagger_dict = spacy_taggers
            try:
                if 'accurate' in self.tagger_option:
                    import spacy
                    return spacy.load(tagger_dict[self.lang]['spacy:accurate'])
                elif 'efficient' in self.tagger_option:
                    import spacy
                    return spacy.load(tagger_dict[self.lang]['spacy:efficient'])
            except OSError:
                raise Exception(f'You need to download the training model for SpaCy before you can use it.\n See https://spacy.io/models for how to download a tagger.')
        elif 'stanza' in self.tagger_option:
            try:
                import stanza
                return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=True)
            except:
                stanza.download(self.lang)
                return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=False)
        

    def find_indexed_file(self):
        if os.path.exists(f'{self.basename}/corpus.elix'):
            return True
        return False

    def create_indexed_file(self):
        # Create folder that will contain ELIX.
        if not os.path.exists(self.basename):
            os.mkdir(self.basename)
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
        with open(f'{self.basename}/corpus.elix', 'w', encoding='utf-8') as file_out:
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
                    print(f'\rTagging Lines of Text: {idx} ({round(idx/total_lines*100, 1)}%)', end='')
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

    def create_word_list(self):
        elixir = pandas.read_csv(f'{self.basename}/corpus.elix', sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000, keep_default_na=False)
        # word_tracking will contain each words. Once it hits correct size or end of sentence, then reset the words.
        categories = ['text', 'lower', 'lemma', 'pos']
        word_dict = {}
        print('Adding Words to Frequency Word List...')
        # Iterate through each chunk of the elix file.
        for chunk in elixir:
            for w in chunk.to_dict('records'):
                
                key = '\t'.join([w[i]for i in categories])
                if key not in word_dict:
                    word_dict[key] = 0

                word_dict[key] += 1

        print('Sorting Frequency Word List...')
        sorted_dict = sorted(word_dict.items(), key=lambda item: item[1], reverse=True)

        with open(f'{self.basename}/word_frequency.elix', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, 
                                delimiter='\t',
                                quotechar='|',
                                quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['text', 'lower', 'lemma', 'pos', 'freq'])
            for k, v in sorted_dict:
                writer.writerow([*k.split('\t'), v])

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
            normal_words = chunk[~chunk['pos'].isin(self.punct_pos)]
            self.word_count += normal_words.shape[0]
        if self.verbose:
            print(f'{self.word_count} words have been loaded!')

    def search(self, search_string, **kwargs):
        # Parse kwargs
        text_filter = kwargs['text_filter'] if 'text_filter' in kwargs else None
        verbose = kwargs['verbose'] if 'verbose' in kwargs else None
        regex = kwargs['regex'] if 'regex' in kwargs else False
        return SearchResults(self.filename, search_string, self.word_count, punct_pos=self.punct_pos, verbose=verbose, text_filter=text_filter, regex=regex)


    def build_corpus(self, **kwargs):
        # HOME PAGE DATA
        # Build Word Frequency
        
        # Build Word Normalized Frequency

        # Build Word Dispersion

        # WORD-BY-WORD DATA
        # Build Frequency Distribution

        # Build Collocates

        # Build Sentences

        # Build KWIC Lines

        # Build Clusters
        pass

    # Calculates the word frequency list.
    def word_frequency(self, **kwargs):
        return NGrams(self.filename,
                      size=1,
                      group_by=kwargs['group_by'] if 'group_by' in kwargs else 'lower', 
                      sep=kwargs['sep'] if 'sep' in kwargs else ' ', 
                      text_filter=kwargs['text_filter'] if 'text_filter' in kwargs else None,
                      punct_pos=self.punct_pos, 
                      chunk_num=self.chunk_num)

    # Calculates the ngram frequency list.
    def ngrams(self, size, **kwargs):
        return NGrams(self.filename, 
                      size, 
                      group_by=kwargs['group_by'] if 'group_by' in kwargs else 'lower', 
                      sep=kwargs['sep'] if 'sep' in kwargs else ' ', 
                      text_filter=kwargs['text_filter'] if 'text_filter' in kwargs else None, 
                      punct_pos=self.punct_pos, 
                      chunk_num=self.chunk_num)


