import pandas as pd
import numpy as np
import nltk
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import matplotlib.pyplot as plt
import seaborn as sns

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK 'punkt' tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("Downloading NLTK 'averaged_perceptron_tagger'...")
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading NLTK 'wordnet'...")
    nltk.download('wordnet', quiet=True)

try:
    nltk.data.find('taggers/universal_tagset')
except LookupError:
    print("Downloading NLTK 'universal_tagset'...")
    nltk.download('universal_tagset', quiet=True)

pos_map = {'ADJ': 'a', 'ADV': 'r', 'NOUN': 'n', 'VERB': 'v'}
lemmatizer = WordNetLemmatizer()

def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tagged = nltk.pos_tag(tokens, tagset='universal')
    return ' '.join(lemmatizer.lemmatize(w, pos=pos_map.get(t, 'n')) for w, t in tagged if w.isalnum())

print("Starting evaluation...")

data_path = "intents_data.csv"
try:
    df = pd.read_csv(data_path)
except FileNotFoundError:
    print(f"Error: Could not find {data_path}. Make sure it's in the same directory.")
    exit()

df['Subintent'] = df['Subintent'].fillna('none')
print(f"Loaded {len(df)} intent phrases.")

print("Preprocessing data...")
df['processed_phrase'] = df['Phrase'].apply(preprocess)

X = df['processed_phrase']
y = df['Intent']
# I don't see a reason to test subintents as they should be already matched from the primary

labels = sorted(y.unique())

print("Splitting data into 70-30 train-test split")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.3, 
    random_state=42, # just in case
    stratify=y
)

print("Training vectorizer on training data...")
vectorizer = TfidfVectorizer(analyzer='word')
tfidf_train = vectorizer.fit_transform(X_train)
tfidf_test = vectorizer.transform(X_test)

print("Getting predictions for the test set...")
similarity_matrix = cosine_similarity(tfidf_test, tfidf_train)
best_match_indices = np.argmax(similarity_matrix, axis=1)
y_pred = [y_train.iloc[i] for i in best_match_indices]

print("\n--- PERFORMANCE RESULTS ---")

accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")
print("-" * 27)
 
print("Classification Report:")
print(classification_report(y_test, y_pred, labels=labels))
print("-" * 27)

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred, labels=labels)
plt.figure(figsize=(10, 8))
sns.heatmap(
    cm, 
    annot=True, 
    fmt='d',  # format as integers
    cmap='Blues', 
    xticklabels=labels, 
    yticklabels=labels
)
plt.title('Intent Classifier Confusion Matrix')
plt.ylabel('True Intent')
plt.xlabel('Predicted Intent')
plt.tight_layout()
plot_filename = "intent_confusion_matrix.png"
plt.savefig(plot_filename)
print(f"\nConfusion matrix saved as '{plot_filename}'")
plt.show()

print("Evaluation complete")
