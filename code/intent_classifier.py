import pandas as pd
import numpy as np
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
#from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

pos_map = {'ADJ': 'a', 'ADV': 'r', 'NOUN': 'n', 'VERB': 'v'}

# Very similar to the labs
# Originally each of the modules (apart from QA/Small Talk) had their own intent classification as seen here
# This would determine the user's general intent, and the speciailzed ones would determine the subintent
# Instead I decided to just do subintents here and combine all the intents and subintents into one big intent database
class IntentClassifier:
    def __init__(self, data_path="datasets/intents_data.csv"):
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = None
        self.intent_phrases_tfidf = None
        self.phrases = []
        self.intents = []
        self.subintents = []
        self._load_and_train(data_path)

    def _preprocess(self, text):
        tokens = nltk.word_tokenize(text.lower())
        tagged = nltk.pos_tag(tokens, tagset='universal')
        return ' '.join(self.lemmatizer.lemmatize(w, pos=pos_map.get(t, 'n')) for w, t in tagged if w.isalnum())

    def _load_and_train(self, data_path):
        try:
            df = pd.read_csv(data_path)
            df['Subintent'] = df['Subintent'].fillna('none') 
            self.phrases = [self._preprocess(p) for p in df['Phrase'].tolist()]
            self.intents = df['Intent'].tolist()
            self.subintents = df['Subintent'].tolist()
            self.vectorizer = TfidfVectorizer(analyzer='word')
            self.intent_phrases_tfidf = self.vectorizer.fit_transform(self.phrases)
        # I've never actually managed to cause this, unless you mess with the actual CSV, but you find a way just by running Maila please tell me
        except Exception as e:
            print(f"[SYSTEM ERROR]: Error with loading or training intent data: {e}")
            self.vectorizer = None

    def classify(self, query, threshold):
        if self.vectorizer is None:
            return "SystemError", "none", 0.0
        processed_query = self._preprocess(query)
        if not processed_query.strip():
            return "SystemError", "none", 0.0
        query_tfidf = self.vectorizer.transform([processed_query])
        if query_tfidf.sum() == 0:
            return "Unrecognized", "none", 0.0
        similarity_scores = cosine_similarity(query_tfidf, self.intent_phrases_tfidf)[0]
        best_match_index = np.argmax(similarity_scores)
        best_score = similarity_scores[best_match_index]
        if best_score >= threshold:
            return self.intents[best_match_index], self.subintents[best_match_index], best_score
        else:
            return "Unrecognized", "none", best_score