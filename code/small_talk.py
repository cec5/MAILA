import pandas as pd
import numpy as np
import nltk
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
#from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

pos_map = {'ADJ': 'a', 'ADV': 'r', 'NOUN': 'n', 'VERB': 'v'}

class SmallTalkHandler:
    def __init__(self, data_path="datasets/small_talk.csv"):
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = None
        self.questions_tfidf = None
        self.questions = []
        self.answers = []
        self._load_and_train(data_path)

    def _preprocess(self, text):
        tokens = nltk.word_tokenize(text.lower())
        tagged = nltk.pos_tag(tokens, tagset='universal')
        return ' '.join(self.lemmatizer.lemmatize(w, pos=pos_map.get(t, 'n')) for w, t in tagged if w.isalnum())

    def _load_and_train(self, data_path):
        try:
            df = pd.read_csv(data_path)
            self.questions = [self._preprocess(q) for q in df['Question'].tolist()]
            self.answers = df['Answer'].tolist()
            self.vectorizer = TfidfVectorizer(analyzer='word')
            self.questions_tfidf = self.vectorizer.fit_transform(self.questions)
        except Exception as e:
            print(f"[SYSTEM ERROR]: Error loading small talk data: {e}")
            self.vectorizer = None

    def get_small_talk_response(self, query, threshold):
        if self.questions_tfidf is None or self.vectorizer is None:
            return "[SYSTEM ERROR]: Error with small talk processing"
        processed_query = self._preprocess(query)
        if not processed_query.strip():
            return "[SYSTEM ERROR]: Error with small talk processing"
        query_tfidf = self.vectorizer.transform([processed_query])
        if query_tfidf.sum() == 0:
            return "[SYSTEM ERROR]: No match for query within small talk"  
        similarity_scores = cosine_similarity(query_tfidf, self.questions_tfidf)[0]
        best_match_index = np.argmax(similarity_scores)
        best_score = similarity_scores[best_match_index]
        if best_score >= threshold:
            responses = [r.strip() for r in self.answers[best_match_index].split("|")]
            return random.choice(responses)
        else:
            return "[SYSTEM ERROR]: Error with small talk processing"
