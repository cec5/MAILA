import random

class Discoverability:
    def __init__(self):
        self.templates = {
            "exit_flow": [
                "Very well.",
                "Okay, sounds good.",
                "Alright, cancelling that.",
                "No problem. Let's drop it.",
                "Got it. Moving on."
            ],
            "general_help_loop_reply": [
                "I can certainly tell you more, just specify what you would like me to elaborate on! Commands, identification, or my capabilities?",
                "Happy to help! What are you interested in: my commands, identification, or general capabilities?",
                "Sure thing. I can give details on my commands, how identification works, or what I'm capable of. What sounds good?",
                "Absolutely. Which topic can I detail for you? Commands, identification, or my capabilities?"
            ],
            "general_help_loop_error": [
                "I couldn't understand your reply, do you still need general help?",
                "Sorry, I didn't get that. Are you still looking for help?",
                "I'm not sure what that means. Did you still want help with something?",
                "Hmm, I didn't follow. Do you still need assistance?"
            ],
            "capabilities_help_reply": [
                "Alright, ask me about small talk, question and answering, identification, or email services for more information.",
                "Okay, I can give more info on: small talk, question answering, identification, or my email services. Which one?",
                "Sure. Feel free to ask for details on small talk, Q&A, identification, or the email services.",
                "Sounds good. I can elaborate on small talk, question answering, identity management, or the email service. Just let me know."
            ],
            "capabilities_help_smalltalk": [
                "I'm happy to have small talk if that's what you would like, just talk to me!",
                "Yep, I can chat about all sorts of things. Feel free to start a conversation!",
                "Of course. I'm always ready for a friendly chat. What's on your mind?"
            ],
            "capabilities_help_qa": [
                "I have a wide variety of knowledge! Ask me something and I'll do my best to answer it!",
                "I can answer all sorts of general knowledge questions. Try asking me something like 'what is the capital of France?'",
                "My question answering is pretty good. Ask me about facts, definitions, or people!"
            ],
            "capabilities_help_email": [
                "I am capable of generating you a temporary email for use! As well as managing emails received at that address, if you wish to get started, ask me to generate you an email!",
                "My main function! I can create a temporary email for you. You can then use me to list, read, download, or delete emails. Just ask me to 'start a new session'!",
                "That's my specialty. I can create a disposable email address for you. From there, you can ask me to 'check my inbox', 'view email 1', and so on."
            ],
            "capabilities_help_error": [
                "I couldn't understand your reply, do you still need info regarding my capabilities?",
                "Sorry, didn't catch that. Still want to know about my capabilities?",
                "I'm not sure what you mean. Did you want more info on my features?",
                "I didn't follow. Are you still interested in my capabilities?"
            ],
            "HelpGeneral": [
                "What do you need help with? Would you like any further information on commands, identification, or my capabilities?",
                "I can help. Are you interested in my commands, identification, or my capabilities?",
                "How can I assist? I can provide info on commands, identification, or my general capabilities.",
                "I'd be glad to help. I can explain my commands, identity features, or my other capabilities. What piques your interest?"
            ],
            "HelpCommands": [
                "I have five universal commands:\nWHERE AM I: tells you what state the chatbot current is in.\nGO BACK: rewinds to the last step\nCANCEL: cancels any ongoing action in its entirety\nREPEAT: repeats the prompt of the current task.\nWHAT NOW: gives you options on what to do next.",
                "My universal commands are:\n  - 'where am i?' (tells you the current state)\n  - 'go back' (goes back one step)\n  - 'cancel' (stops any task)\n  -  'repeat' (repeats the prompt of the current task)\n  -  'what now' (tells you what to do next based on the current state)",
                "You can use these commands anytime:\n'where am i?' will show your current state.\n'go back' reverts one step in a task.\n'cancel' exits the current task completely\n'repeat' repeats the dialogue of the current task.\n'what now' informs you of how to progress from the current task."
            ],
            "Identification": [
                "If you tell me your name or tell me that you want to set your name, I am capable of remembering it. You can also change your name, or tell me to forget it entirely.",
                "I can remember your name! Just say 'my name is...' or 'call me...'. You can also ask me to 'change my name' or 'forget my name' later.",
                "Just tell me your name, and I'll remember it. You can also tell me to 'forget my name' to clear it."
            ],
            "Capabilities": [
                "I am capable of basic small talk, question and answering, identity management, and generating you a temporary email, would you like any further information on any of these?",
                "My main features include small talk, answering questions, managing your name, and providing temporary email services. Want to know more about any of them?",
                "I can do a few things: chat casually, answer general questions, remember who you are, and create temporary email addresses. Would you like details on any of those?",
                "My functions include: casual chat, answering questions, remembering your name, and managing a temporary email inbox. I can give you more info on any of these."
            ],
            "Purpose": [
                "I am Maila, an AI-powered Chatbot designed for a class at the University of Nottingham. I am designed to assist you with setting up a temporarily email address in an conversational manner.",
                "My name is Maila. I'm a chatbot for a University of Nottingham project, here to help you get and manage a temporary email address.",
                "I am Maila, a prototype chatbot from the University of Nottingham. My purpose is to help you create and manage a temporary email inbox."
            ],
            "Error": [
                "I unfortunately can't understand what you are asking for help with.",
                "Sorry, I'm not sure what you need help with.",
                "I don't have a help topic for that, my apologies.",
                "I'm not sure which help topic you're asking about."
            ]
        }

    def _get_random_response(self, key):
        return random.choice(self.templates.get(key, ["An error occurred."]))

    def get_discoverability_response(self, query, subintent, current_state="normal"):
        query = query.strip()

        if current_state == "general_help_loop":
            if any(word in query.lower() for word in ["no","nevermind"]):
                return (self._get_random_response("exit_flow"), "normal")
            elif any(word in query.lower() for word in ["commands","command"]):
                subintent = "HelpCommands"
            elif any(word in query.lower() for word in ["identification","name","identity"]):
                subintent = "Identification"
            elif any(word in query.lower() for word in ["capable","capabilities","do"]):
                subintent = "Capabilities"
            elif any(word in query.lower() for word in ["yes", "affirmative"]):
                return (self._get_random_response("general_help_loop_reply"), "general_help_loop")
            else:
                return (self._get_random_response("general_help_loop_error"), "general_help_loop")
        elif current_state == "capabilities_help":
            if any(word in query.lower() for word in ["no","nevermind"]):
                return (self._get_random_response("exit_flow"), "normal")
            elif any(word in query.lower() for word in ["yes","ok","alright"]):
                return (self._get_random_response("capabilities_help_reply"), "capabilities_help")
            elif any(word in query.lower() for word in ["small","talk","talking","conversation","chat","chatting"]):
                return (self._get_random_response("capabilities_help_smalltalk"), "normal")
            elif any(word in query.lower() for word in ["question","questions","answer","answers","answering"]):
                return (self._get_random_response("capabilities_help_qa"), "normal")
            elif any(word in query.lower() for word in ["identification","name","identity"]):
                subintent = "Identification"
            elif any(word in query.lower() for word in ["email","emails"]):
                return (self._get_random_response("capabilities_help_email"), "normal") 
            else:
                return (self._get_random_response("capabilities_help_error"), "capabilities_help")
        if subintent == "HelpGeneral":
            return (self._get_random_response("HelpGeneral"), "general_help_loop")
        elif subintent == "HelpCommands":
            return (self._get_random_response("HelpCommands"), "normal")
        elif subintent == "Identification":
            return (self._get_random_response("Identification"), "normal")
        elif subintent == "Capabilities":
            return (self._get_random_response("Capabilities"), "capabilities_help")
        elif subintent == "Purpose":
            return (self._get_random_response("Purpose"), "normal")
        elif subintent == "HelpSmallTalk":
            return (self._get_random_response("capabilities_help_smalltalk"), "normal")
        elif subintent == "HelpQA":
            return (self._get_random_response("capabilities_help_qa"), "normal")
        elif subintent == "HelpEmail":
            return (self._get_random_response("capabilities_help_email"), "normal")
        else:
            return (self._get_random_response("Error"), "normal")
