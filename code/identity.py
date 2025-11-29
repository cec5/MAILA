from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import random

class IdentityManagement:
    def __init__(self):
        self.stopwords = set(stopwords.words('english'))
        self.name_ignore = ["call","name","my","to","please","yes","is","i","am","know","who","tell","change","want","wish","rename","switch","update","remember"]
        self.templates = {
            "confirm_name_change": [
                "Very well! Simply tell me your name please!",
                "Okay, I'm ready. What would you like me to call you?",
                "Sure thing. Just type your name."
            ],
            "cancel_flow": [
                "Alright then!",
                "Okay, no problem.",
                "Got it, cancelled."
            ],
            "confirm_name_change_error": [
                "I'm sorry, did you want to set your name?",
                "I didn't quite catch that. Was that a 'yes' or 'no'?",
                "My apologies, I'm not sure if you want to proceed. Please say 'yes' or 'no'."
            ],
            "set_name_success": [
                "Got it, you are {new_name}!",
                "Pleased to meet you, {new_name}!",
                "Okay, I'll call you {new_name} from now on."
            ],
            "set_name_error": [
                "I didn't quite get that, please type in your name below!",
                "Sorry, I couldn't understand that. Please just type your name.",
                "I'm afraid I didn't get a name. Could you try again?"
            ],
            "get_name_known": [
                "You are {username}.",
                "I have you down as {username}.",
                "You told me your name is {username}."
            ],
            "get_name_unknown": [
                "I don't think you've told me your name yet, would you like to set it?",
                "I don't have a name for you. Would you like to tell me what to call you?",
                "You haven't told me your name. Want to set it now?"
            ],
            "set_name_direct_change": [
                "{username}, you want to be called {new_name} now? Very well!",
                "Okay, {username}. I've updated your name to {new_name}.",
                "Got it. I'll call you {new_name} instead of {username} from now on."
            ],
            "set_name_direct_new": [
                "Nice to meet you, {new_name}. I’ll remember you.",
                "Got it. I'll remember that your name is {new_name}.",
                "{new_name}, is it? A pleasure to meet you!"
            ],
            "set_name_direct_error": [
                "I couldn't quite catch your name there.",
                "Sorry, I heard you, but I wasn't able to extract a name.",
                "I'm not sure what name you'd like me to use."
            ],
            "prompt_for_name": [
                "Very well! Type in your name below!",
                "Okay, what is the new name you'd like me to use?",
                "Sure, just let me know what your new name is."
            ],
            "delete_name_success": [
                "I’ve forgotten your name, {username}.",
                "Okay {username}, I've cleared your name from my memory.",
                "Alright, I no longer have a name stored for you."
            ],
            "delete_name_error": [
                "Unfortunately, I can't forget a name that I don't know.",
                "I don't have a name for you, so there's nothing for me to forget.",
                "I'd be happy to, but I don't know your name in the first place."
            ],
            "unrecognized_identity": [
                "I’m not sure what you mean about your name.",
                "I'm a bit confused about that request regarding your name.",
                "I didn't quite understand that identity request."
            ],
            "system_error_identity": [
                "[SYSTEM ERROR]: Error in identity processing.",
                "[SYSTEM ERROR]: An identity handling error occurred."
            ]
        }
        
    def _get_random_response(self, key, **kwargs):
        try:
            template = random.choice(self.templates[key])
            return template.format(**kwargs)
        except KeyError:
            return "Sorry, I had an error generating a response."
        except Exception:
            return random.choice(self.templates[key])

    def _extract_possible_name(self, query):
        tokens = word_tokenize(query.lower())
        filtered = [t for t in tokens if t.isalpha() and t not in self.name_ignore and t not in self.stopwords]
        if not filtered:
            return None
        return filtered[-1].capitalize()
    def get_identity_response(self, query, username, subintent, current_state="normal"):
        query = query.strip()
        response = ""
        if current_state == "awaiting_name_confirm":
            if any(word in query.lower() for word in ["yes","ok","alright"]):
                response = self._get_random_response("confirm_name_change")
                return (response, username, "awaiting_name")
            elif any(word in query.lower() for word in ["no","nevermind"]):
                response = self._get_random_response("cancel_flow")
                return (response, username, "normal")
            else:
                response = self._get_random_response("confirm_name_change_error")
                return (response, username, "awaiting_name_confirm")
        elif current_state == "awaiting_name":
            if query:
                new_name = query.strip().capitalize()
                response = self._get_random_response("set_name_success", new_name=new_name)
                return (response, new_name, "normal")
            else:
                response = self._get_random_response("set_name_error")
                return (response, username, "awaiting_name")
        if subintent == "Identification":
            if username:
                response = self._get_random_response("get_name_known", username=username)
                return (response, username, "normal")
            else:
                response = self._get_random_response("get_name_unknown")
                return (response, username, "awaiting_name_confirm")
        elif subintent == "NameDirect":
            new_name = self._extract_possible_name(query)
            if new_name and username:
                response = self._get_random_response("set_name_direct_change", username=username, new_name=new_name)
                return (response, new_name, "normal")
            elif new_name:
                response = self._get_random_response("set_name_direct_new", new_name=new_name)
                return (response, new_name, "normal")
            else:
                response = self._get_random_response("set_name_direct_error")
                return (response, username, "normal")
        elif subintent == "NameChange":
            response = self._get_random_response("prompt_for_name")
            return (response, username, "awaiting_name")
        elif subintent == "NameDelete":
            if username:
                response = self._get_random_response("delete_name_success", username=username)
                return (response, None, "normal")
            else:
                response = self._get_random_response("delete_name_error")
                return (response, username, "normal")
        elif subintent == "Unrecognized":
            response = self._get_random_response("unrecognized_identity")
            return (response, username, "normal")
        elif subintent == "SystemError":
            response = self._get_random_response("system_error_identity")
            return (response, username, "normal")
        else:
            response = self.templates.get("unrecognized_identity", ["I'm not sure how to handle that request about your name."])[0]
            return (response, username, "normal")