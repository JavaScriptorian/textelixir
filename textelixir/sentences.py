import pandas
import re
from .exports import export_as_txt 
from .filter_indices_by_block import *  # filter_indices_by_block(results, block_num)
from .get_word_data import *            # get_word_data(basename, word_types)
from .get_full_citation import *        # get_full_citation(df)

class Sentences:
    #SECTION: Init
    def __init__(self, filename, results, group_by, search_string):
        self.filename = filename
        self.basename = re.sub(r'^(.+)/[^/]+$', r'\1', self.filename)
        self.results = results
        self.group_by = group_by
        self.search_string = search_string
        self.sentences = self.get_sentences(self.results)
    #!SECTION


    def get_sentences(self, results):
        sentence_indices = self.get_sentence_indices(results)
        full_sentence_indices = self.get_full_sentence_indices(sentence_indices)
        full_sentences = self.parse_full_sentences(get_word_data(self.basename, ['prefix', self.group_by]), full_sentence_indices)
        return full_sentences


    def get_sentence_indices(self, results):
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        sentence_indices = {}
        unfinished_segments = {}
        for block_num, chunk in enumerate(elixir):        
            curr_indices = filter_indices_by_block(results, block_num)
            for curr_index in curr_indices:
                if len(curr_index) > 1:
                    # Verify that the first and last word are in the same sentence.
                    w1 = chunk.loc[curr_index[0]]
                    w2 = chunk.loc[curr_index[1]]
                    sent_index1 = int(w1.sent_index)
                    sent_index2 = int(w2.sent_index)
                    # Skip this hit if not in the same sentence.
                    if sent_index1 != sent_index2:
                        continue
                    # Verify the first and last word are in the same chunk.
                    if (
                        curr_index[0] >= block_num*1000000 and 
                        curr_index[0] < (block_num*1000000) + 1000000 and
                        curr_index[-1] >= block_num*1000000 and 
                        curr_index[-1] < (block_num*1000000) + 1000000
                        ):
                        if block_num not in sentence_indices:
                            sentence_indices[block_num] = {}
                        
                        if sent_index1 not in sentence_indices[block_num]:
                            sentence_indices[block_num][sent_index1] = [(w, chunk.loc[w].word) for w in curr_index]
                    # If they're in different chunks, then they need to be checked once we are in the next block.
                    else:
                        raise Exception('These indices cross chunk boundaries.')
                else:
                    w = chunk.loc[curr_index[0]]
                    word = w.word
                    sent_index = int(w.sent_index)

                    if block_num not in sentence_indices:
                        sentence_indices[block_num] = {}

                    sentence_indices[block_num][sent_index] = [(curr_index[0], word)]
        return sentence_indices


    def get_full_sentence_indices(self, sentence_indices):
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        full_sentence_indices = {}
        for block_num, chunk in enumerate(elixir):
            # Skip blocks that have no hits.
            if block_num not in sentence_indices:   
                continue 
            curr_sentence_indices = sentence_indices[block_num]

            for sentence_index, hit_words in curr_sentence_indices.items():
                sentence_df = chunk[chunk.sent_index == sentence_index]
                sentence_word_ids = list(sentence_df.word)
                sentence_word_order = list(sentence_df.index)

                if sentence_index not in full_sentence_indices:
                    full_sentence_indices[sentence_index] = { 
                        'hits': [hit_word[0] for hit_word in hit_words], 
                        'ids': list(zip(sentence_word_order, sentence_word_ids)), 
                        'cit': get_full_citation(sentence_df)
                        }
                else:
                    raise Exception('You have hit an undeveloped part of TextElixir. This means that there are two hits in the sentences, but TextElixir has not figured out how to handle two hits in a sentence.')
                    full_sentence_indices[sentence_index]['ids'].extend(sentence_word_ids)
        return full_sentence_indices

    #SECTION: Parse full sentences
    def parse_full_sentences(self, word_data, full_sentence_indices):
        full_sentences = {}
        for sent_id, full_sentence_index_dict in full_sentence_indices.items():
            hits = full_sentence_index_dict['hits']
            citation = full_sentence_index_dict['cit']
            curr_sentence = ''
            for word_order, word_value in full_sentence_index_dict['ids']:
                prefix = word_data['prefix'][word_value]
                text = word_data[self.group_by][word_value]
                if word_order in hits:
                    curr_sentence += f'{prefix}<b>{text}</b>'
                else:
                    curr_sentence += f'{prefix}{text}'
            full_sentences[sent_id] = {'citation': citation, 'sentence': curr_sentence}
        return full_sentences
    #!SECTION
    

