
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
import pickle
from utils import *
from collections import defaultdict
toxic_counter = defaultdict(lambda: 1)
nontoxic_counter = defaultdict(lambda: 1)
from transformers import BertTokenizer

class LR_classifier:
    def __init__(self,c,norm_corpus,tox_corpus):
            self.c=c
            self.norm_corpus=norm_corpus
            self.tox_corpus=tox_corpus
    def cleaning_corpus(c,norm_corpus,tox_corpus):
        vocab = {w for w, _ in c.most_common() if _ > 0} 
        for line in tox_corpus.readlines():
            for w in line.strip().split():
                if w in vocab:
                    corpus_tox=[' '.join[w]]
        for line in norm_corpus.readlines():
            for w in line.strip().split():
                if w in vocab:
                    corpus_norm=[' '.join[w]]
        return corpus_tox,corpus_norm


import numpy as np

class NgramSalienceCalculator():
    def __init__(self, tox_corpus, norm_corpus, use_ngrams=False):
        ngrams = (1, 3) if use_ngrams else (1, 1)
        self.vectorizer = CountVectorizer(ngram_range=ngrams)

        tox_count_matrix = self.vectorizer.fit_transform(tox_corpus)
        self.tox_vocab = self.vectorizer.vocabulary_
        self.tox_counts = np.sum(tox_count_matrix, axis=0)

        norm_count_matrix = self.vectorizer.fit_transform(norm_corpus)
        self.norm_vocab = self.vectorizer.vocabulary_
        self.norm_counts = np.sum(norm_count_matrix, axis=0)
        self.salience(self, feature,'tox', 0.5)
            
class token_toxicity_calc():
    def __init__(self,corpus_tox,corpus_norm):
        model_name = 'bert-base-uncased'
        tokenizer = BertTokenizer.from_pretrained(model_name)
        for text in (corpus_tox):
            for token in tokenizer.encode(text):
                toxic_counter[token] += 1
        for text in (corpus_norm):
            for token in tokenizer.encode(text):
                nontoxic_counter[token] += 1

        token_toxicities = [toxic_counter[i] / (nontoxic_counter[i] + toxic_counter[i]) for i in range(len(tokenizer.vocab))]
        with open('vocabularies/token_toxicities.txt', 'w') as f:
            for t in token_toxicities:
                f.write(str(t))
                f.write('\n')
