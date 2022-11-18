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
    # SECTION: Initialize Class
    def __init__(self, filename=None, lang='en', elixir_filename=None, **kwargs):
        # Parse kwargs
        self.tagger_option = kwargs['tagger_option'] if 'tagger_option' in kwargs else 'stanza:pos'
        self.punct_pos = kwargs['punct_pos'] if 'punct_pos' in kwargs else ['SYM', 'PUNCT', 'SPACE']
        self.verbose = kwargs['verbose'] if 'verbose' in kwargs else True
        self.update_threshold = kwargs['update_threshold'] if 'update_threshold' in kwargs else 10
        # Parse args
        self.filename = filename
        self.lang = lang
        # Create empty tables dictionary
        self.tables = {}

        # Check for pre-loaded ELIX file.
        if isinstance(self.filename, str) and os.path.exists(f'{self.filename}/corpus.tsv'):
            self.basename = self.filename
            self.filename = f'{self.filename}/corpus.tsv'
            self.read_elixir()
        else:
            if isinstance(filename, list):
                self.filename = filename
                self.extension = 'GLOB-' + re.search(r'\.([^\.]+?)$', os.path.basename(filename[0])).group(1).upper()
                self.basename = 'Glob Elixir'
                self.elixir_filename = f'{self.basename}/corpus.tsv'
            else:
                self.extension = re.search(r'\.([^\.]+?)$', os.path.basename(filename)).group(1).upper()
                self.basename = re.sub(r'\.[^\.]+?$', r'', os.path.basename(filename))
                self.elixir_filename = f'{self.basename}/corpus.tsv'
            if self.find_indexed_file() == False:
                self.create_indexed_file()
                self.output_tables()
            self.filename = self.elixir_filename
            self.read_elixir()
    # !SECTION


    # SECTION String Dunder
    def __str__(self):
        return f'Corpus containing {self.word_count} words.'


    def __repr__(self):
        return str(self)
    # !SECTION


    # SECTION Start Tagger
    def initialize_tagger(self):
        if 'spacy' in self.tagger_option:
            # Access tagger table
            tagger_dict = spacy_taggers
            try:
                if 'accurate' in self.tagger_option:
                    import spacy
                    nlp = spacy.load(tagger_dict[self.lang]['spacy:accurate'], disable=['ner', 'parser'])
                    nlp.add_pipe('sentencizer')
                    nlp.max_length = 3000000
                    return nlp
                elif 'efficient' in self.tagger_option:
                    import spacy
                    nlp = spacy.load(tagger_dict[self.lang]['spacy:efficient'], disable=['ner', 'parser'])
                    nlp.add_pipe('sentencizer')
                    nlp.max_length = 3000000
                    return nlp
            except OSError:
                raise Exception(f'You need to download the training model for SpaCy before you can use it.\n See https://spacy.io/models for how to download a tagger.')
        elif 'stanza' in self.tagger_option:
            try:
                import stanza
                return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=True)
            except:
                stanza.download(self.lang)
                return stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma', verbose=False)
    # !SECTION


    # SECTION Find Indexed File
    def find_indexed_file(self):
        if os.path.exists(f'{self.basename}/corpus.tsv'):
            return True
        return False
    # !SECTION

    # SECTION Create Indexed File
    def create_indexed_file(self):
        # SECTION Handle File Formats
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
                for header in headers:
                    self.create_metadata_table(header)
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
            headers.pop(1)
            index_of_text_column = 1
            total_lines = data.shape[0]
            self.create_metadata_table('text_file')
            ibrk = 0
        # !SECTION
        self.create_metadata_table('word')
            
        tagger = self.initialize_tagger()
        
        line_index = 0

        # SECTION Write to corpus.tsv
        with open(f'{self.basename}/corpus.tsv', 'w', encoding='utf-8') as file_out:
            writer = csv.writer(file_out, delimiter='\t')
            ### PRINT HEADERS FOR ELIX FILE ###

            # text\tlower\tpos\tlemma\tprefix
            if self.extension in ['TXT']:
                writer.writerow(['line_index', 'sent_index', 'word_index', 'word'])
            elif self.extension == 'TSV':
                writer.writerow([*headers, 'sent_index', 'word_index', 'word'])
            elif self.extension == 'GLOB-TXT':
                writer.writerow(['text_file', 'sent_index', 'word_index', 'word'])


            sentence_index = 0
            ### GET CURRENT LINE TO TAG ###
            for idx in range(0, total_lines):
                if idx % self.update_threshold == 0:
                    print(f'\rTagging Lines of Text: {idx} ({round(idx/total_lines*100, 1)}%)', end='')
                # Get the text of the line.
                if self.extension == 'TXT':
                    line = data[idx]
                elif self.extension in ['TSV', 'GLOB-TXT']:
                    df_line = data.iloc[idx]
                    line = df_line['text']
                    # Add data to metadata tables
                    header_data = []
                    for header in headers:
                        value_id = self.append_metadata_table(header, df_line[header])
                        header_data.append(value_id)

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
                    word_id = self.append_metadata_table('word', '\t'.join([w['text'], w['text'].lower(), w['pos'], w['lemma'], w['prefix_text']]))
                    if self.extension == 'TXT':
                        output_string = f'{w["line_index"]}\t{w["sentence_index"]}\t{w["word_index"]}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'TSV':
                        # tsv_attributes = "\t".join([self.clean_text(df_line[header]) for header in headers])
                        writer.writerow([*header_data, w['sentence_index'], w['word_index'], word_id])
                        # output_string = f'{tsv_attributes}\t{w["sentence_index"]}\t{w["word_index"]}\t{w["text"]}\t{w["text"].lower()}\t{w["pos"]}\t{w["lemma"]}\t{w["prefix_text"]}'
                    elif self.extension == 'GLOB-TXT':
                        writer.writerow([df_line['text_file'], w['sentence_index'], w['word_index'], word_id])
            print(f'\rTagging Lines of Text: {idx} ({round(idx/total_lines*100, 1)}%)', end='\n')        
        #!SECTION
    # !SECTION


    # SECTION Metadata Tables
    def create_metadata_table(self, table_name):
        self.tables[table_name] = {}

    def append_metadata_table(self, table_name, value):
        # Clean the text of the value before comparing.
        value = self.clean_text(value) if table_name != 'word' else value
        
        # Check to see if the value already exists.
        table = self.tables[table_name]
        if value in table:
            return table[value]
        else:
            table_length = len(table)
            table[value] = table_length
            return table_length

    def output_tables(self):
        for table_name, table in self.tables.items():
            with open(f'{self.basename}/{table_name}.tsv', 'w', encoding='utf-8') as file_out:
                writer = csv.writer(file_out, delimiter='\t')
                if table_name == 'word':
                    writer.writerow(['index', 'text', 'lower', 'pos', 'lemma', 'prefix'])
                else:
                    writer.writerow(['index', 'value'])
                for value, index in table.items():
                    if table_name == 'word':
                        writer.writerow([index, *value.split('\t')])
                    else:
                        writer.writerow([index, value])
                    
    # !SECTION


    # SECTION Clean String
    def clean_text(self, string):
        string = str(string).replace(u'\xa0', u' ')
        string = re.sub(r'[\t\n\r]', r' ', string)
        string = re.sub(r' {2,}', r' ', string)
        return string
    # !SECTION


    # SECTION Read Elixir
    def read_elixir(self):
        if self.verbose:
            print(f'Reading {self.filename}...')
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        self.word_count = 0
        self.chunk_num = 0
        punctuation_word_ids = self.get_metadata('word', pos=[self.punct_pos])
        for chunk in self.elixir:
            self.chunk_num += 1
            normal_words = chunk[~chunk['word'].isin(punctuation_word_ids)]
            self.word_count += normal_words.shape[0]
        if self.verbose:
            print(f'{self.word_count} words have been loaded!')
    # !SECTION


    # SECTION Get Metadata Tables
    def get_metadata(self, table_name, **kwargs):
        # pos
        key = list(kwargs.keys())[0]
        # [ 'SYM', 'PUNCT', 'SPACE' ]
        value = list(kwargs.values())[0]
        # word.tsv
        metadata = pandas.read_csv(f'{self.basename}/{table_name}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        if isinstance(value, list):
            filtered_metadata = metadata[metadata[key].isin(value[0])]
        else:
            filtered_metadata = metadata[metadata[key] == value]
        return filtered_metadata['index'].to_list()
    # !SECTION


    # SECTION Search
    def search(self, search_string, **kwargs):
        # Parse kwargs
        text_filter = kwargs['text_filter'] if 'text_filter' in kwargs else None
        verbose = kwargs['verbose'] if 'verbose' in kwargs else True
        regex = kwargs['regex'] if 'regex' in kwargs else False
        group_by = kwargs['group_by'] if 'group_by' in kwargs else 'lower'
        return SearchResults(self.filename, search_string, self.word_count, punct_pos=self.punct_pos, verbose=verbose, text_filter=text_filter, regex=regex, group_by=group_by)
    # !SECTION


    # SECTION Word Frequency
    # Calculates the word frequency list.
    def word_frequency(self, **kwargs):
        return NGrams(self.filename,
                      size=1,
                      group_by=kwargs['group_by'] if 'group_by' in kwargs else 'lower', 
                      sep=kwargs['sep'] if 'sep' in kwargs else ' ', 
                      text_filter=kwargs['text_filter'] if 'text_filter' in kwargs else None,
                      punct_pos=self.punct_pos, 
                      chunk_num=self.chunk_num)
    # !SECTION


    # SECTION Ngrams
    # Calculates the ngram frequency list.
    def ngrams(self, size, **kwargs):
        return NGrams(self.filename, 
                      size, 
                      group_by=kwargs['group_by'] if 'group_by' in kwargs else 'lower', 
                      sep=kwargs['sep'] if 'sep' in kwargs else ' ', 
                      text_filter=kwargs['text_filter'] if 'text_filter' in kwargs else None, 
                      punct_pos=self.punct_pos, 
                      chunk_num=self.chunk_num)
    # !SECTION

