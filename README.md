# MAILA: An AI-Powered Implementation of Guerrilla Mail

## Overview

Meet Maila (My-La), a Python-based chatbot built for **Human-AI Interaction (COMP 3074)** at the **University of Nottingham**!

It features a graphical user interface (GUI) built with Tkinter and is designed to act as a conversational assistant. Its primary function is to help users create and manage temporary (disposable) email addresses by interacting with the Guerrilla Mail API.

### Core Features

* **Email Management:** Allows users to start a new temporary email session, restore a previous session, list emails from their inbox, view specific emails, delete emails, and download email content.
* **Q&A:** Answers general knowledge questions based on a provided `question_answer.csv` dataset.
* **Small Talk:** Engages in basic casual conversation using a `small_talk.csv` dataset.
* **Identity Management:** Can remember, change, or forget a user's name.
* **Discoverability:** Can explain its own features and commands (e.g., "what can you do?", "help").
* **Intent Classification:** Understands user requests and categorizes them into intents like "Email," "SmallTalk," "QuestionAnswering," "IdentityManagement," or "Discoverability".
* **State Management:** Manages a conversational state, allowing for multi-step tasks like confirming actions or prompting for more information.

---

## Requirements

### 1. Python 3

The application is written in Python 3.

### 2. Python Packages

The following external Python libraries are required. You can install them using pip (e.g., `pip install pandas`):

* `pandas`
* `numpy`
* `scikit-learn`
* `nltk`
* `requests`

### 3. NLTK Data Downloads

The application uses NLTK for text processing. You must download the required data packets. You can do this by running a Python interpreter and entering the following commands:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')
nltk.download('wordnet')
```
