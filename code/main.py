import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from intent_classifier import IntentClassifier
from small_talk import SmallTalkHandler
from question_answer import QAHandler
from identity import IdentityManagement
from discoverability import Discoverability
from transaction import EmailHandler, EMAIL_AWAITING_STATES, EMAIL_LOOP_STATES

BG_COLOR = "#ece5dd"
CHAT_BG = "#ffffff"
BOT_COLOR = "#ffffff"
USER_COLOR = "#dcf8c6"
TEXT_COLOR = "#111b21"
TIME_COLOR = "#667781"
BUTTON_BG = "#128c7e"
BUTTON_FG = "#ffffff"
FONT = ("Helvetica", 11)
FONT_BOLD = ("Helvetica", 11, "bold")

class EmailViewer(tk.Toplevel):
    def __init__(self, master, email_data):
        super().__init__(master)
        subject = email_data.get('mail_subject', 'No Subject')
        sender = email_data.get('mail_from', 'Unknown Sender')
        body = email_data.get('mail_body', 'No content.')
        self.title(f"Email Viewer - {subject[:40]}...")
        self.geometry("700x550")
        self.configure(bg=BG_COLOR)
        header_frame = tk.Frame(self, bg=CHAT_BG)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        tk.Label(
            header_frame, 
            text="From:", 
            font=FONT_BOLD, 
            bg=CHAT_BG, 
            fg=TEXT_COLOR
        ).pack(anchor='w', padx=10, pady=(5, 0))
        tk.Label(
            header_frame, 
            text=sender, 
            font=FONT, 
            bg=CHAT_BG, 
            fg=TEXT_COLOR, 
            justify='left'
        ).pack(anchor='w', padx=10, pady=(0, 5))
        tk.Label(
            header_frame, 
            text="Subject:", 
            font=FONT_BOLD, 
            bg=CHAT_BG, 
            fg=TEXT_COLOR
        ).pack(anchor='w', padx=10, pady=(5, 0))
        tk.Label(
            header_frame, 
            text=subject, 
            font=FONT, 
            bg=CHAT_BG, 
            fg=TEXT_COLOR, 
            justify='left'
        ).pack(anchor='w', padx=10, pady=(0, 10))
        body_frame = tk.Frame(self, bg=CHAT_BG)
        body_frame.pack(expand=True, fill='both', padx=10, pady=5)
        txt_area = scrolledtext.ScrolledText(
            body_frame, 
            wrap=tk.WORD, 
            undo=True,
            bg=CHAT_BG,
            fg=TEXT_COLOR,
            font=FONT,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=10
        )
        txt_area.pack(expand=True, fill='both')
        txt_area.insert(tk.INSERT, body)
        txt_area.configure(state='disabled')
        tk.Button(
            self, 
            text="Close", 
            command=self.destroy,
            font=FONT_BOLD,
            bg="#128c7e",
            fg="#ffffff",
            relief=tk.FLAT,
            activebackground="#075e54",
            activeforeground="#ffffff"
        ).pack(pady=10)
        self.transient(master)
        self.grab_set()
        self.lift()

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Maila Chatbot")
        self.root.geometry("420x600")
        self.root.configure(bg=BG_COLOR)
        self.username = None
        self.session_id = None
        self.email_address = None
        self.chat_stack = ["normal"]
        self.state_prompts = {}
        self.IDENTITY_TASK_STATES = {"awaiting_name", "awaiting_name_confirm"}
        self.DISCOVER_TASK_STATES = {"general_help_loop", "capabilities_help"}
        self.EMAIL_TASK_STATES = set(EMAIL_LOOP_STATES + EMAIL_AWAITING_STATES)
        self.EMAIL_LOOP_STATES = set(EMAIL_LOOP_STATES)
        self.EMAIL_AWAITING_STATES = set(EMAIL_AWAITING_STATES)
        self.intent_classifier = IntentClassifier()
        self.small_talk_handler = SmallTalkHandler()
        self.qa_handler = QAHandler()
        self.identity_handler = IdentityManagement()
        self.discoverability_handler = Discoverability()
        self.email_handler = EmailHandler()
        self.create_widgets()
        self.add_chat_message("Hello! I am Maila, let's chat!", "bot")
        self.what_now_prompts = {
            "normal": "You can chat with me, ask a question, ask for help, or manage your temporary email (e.g., 'start a new session').",
            "awaiting_name_confirm": "You can say 'yes' to confirm setting your name, or 'no' to cancel.",
            "awaiting_name": "You can type in the name you'd like me to call you, or say 'cancel'.",
            "general_help_loop": "You can ask about 'commands', 'identification', or 'capabilities'. You can also say 'no' to exit help.",
            "capabilities_help": "You can ask for more info on 'small talk', 'Q&A', 'identification', or 'email'. You can also say 'no' to exit.",
            "email_manage_loop": "You are in your email session. You can say 'list emails', 'view [number]', 'delete [number]', 'download [number]', or 'end session'.",
            "awaiting_session_start_confirm": "You can say 'yes' to create a new temporary email session, or 'no' to decline.",
            "awaiting_session_restore_confirm": "You can say 'yes' to try again, 'no' to cancel, or just enter your session ID.",
            "awaiting_session_restore": "You can type or paste your 24-character session ID, or say 'cancel'.",
            "awaiting_session_end_confirm": "You can say 'yes' to permanently end your session, or 'no' to keep it active.",
            "awaiting_view_index": "You can enter the number (index) of the email you want to read, or say 'cancel'.",
            "awaiting_delete_index": "You can enter the email number(s) to delete (e.g., '1', '1, 3', '2-5', or 'all'), or say 'cancel'.",
            "awaiting_download_index": "You can enter the email number(s) to download (e.g., '1', '1, 3', '2-5', or 'all'), or say 'cancel'.",
            "awaiting_delete_all_confirm": "You must say 'yes' to confirm deleting ALL emails, or 'no' to cancel. This cannot be undone."
        }

    def create_widgets(self):
        self.chat_frame = tk.Frame(self.root, bg=CHAT_BG, bd=0)
        self.chat_frame.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            bg=CHAT_BG,
            fg=TEXT_COLOR,
            font=FONT,
            relief=tk.FLAT,
            state=tk.DISABLED,
            padx=10,
            pady=10
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        self.chat_history.tag_configure("user_bubble", background=USER_COLOR, justify='right', lmargin1=80, lmargin2=80, rmargin=10, spacing1=3, spacing2=1, spacing3=3)
        self.chat_history.tag_configure("bot_bubble", background=BOT_COLOR, justify='left', lmargin1=10, lmargin2=10, rmargin=80, spacing1=3, spacing2=1, spacing3=3)
        self.chat_history.tag_configure("user_name", justify='right', font=FONT_BOLD, foreground="#000000", spacing1=6, spacing3=2)
        self.chat_history.tag_configure("bot_name", justify='left', font=FONT_BOLD, foreground="#000000", spacing1=6, spacing3=2)
        self.chat_history.tag_configure("timestamp_right", justify='right', foreground=TIME_COLOR, font=("Helvetica", 8), spacing1=2, spacing3=6)
        self.chat_history.tag_configure("timestamp_left", justify='left', foreground=TIME_COLOR, font=("Helvetica", 8), spacing1=0, spacing3=6)
        input_frame = tk.Frame(self.root, bg=BG_COLOR, pady=6)
        input_frame.pack(fill=tk.X, padx=10)
        self.user_input = tk.Entry(
            input_frame,
            font=FONT,
            bg="#ffffff",
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            bd=2,
            highlightthickness=1,
            highlightbackground="#cccccc",
            highlightcolor="#cccccc"
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 8))
        self.user_input.bind("<Return>", self.on_send_pressed)
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=FONT_BOLD,
            bg=BUTTON_BG,
            fg=BUTTON_FG,
            relief=tk.FLAT,
            activebackground="#075e54",
            activeforeground="#ffffff",
            command=self.on_send_pressed
        )
        self.send_button.pack(side=tk.RIGHT, ipadx=10, ipady=6)

    def on_send_pressed(self, event=None):
        query = self.user_input.get().strip()
        if not query:
            return
        self.user_input.delete(0, tk.END)
        self.add_chat_message(query, "user")
        self.root.after(200, self.get_bot_response, query) # makes it realistic I guess?

    def add_chat_message(self, message, sender):
        self.chat_history.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")
        if sender == "user":
            name = self.username.upper() if self.username else "YOU"
            self.chat_history.insert(tk.END, f"{name}\n", "user_name")
            self.chat_history.insert(tk.END, f"{message}\n", "user_bubble")
            self.chat_history.insert(tk.END, f"{timestamp}\n", "timestamp_right")
        else:
            self.chat_history.insert(tk.END, "MAILA\n", "bot_name")
            self.chat_history.insert(tk.END, f"{message}\n", "bot_bubble")
            self.chat_history.insert(tk.END, f"{timestamp}\n", "timestamp_left")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    # generally, we want to the pop the entire group if the chain is completed
    def manage_state(self, new_state, prompt_to_save=None):
            current_state = self.chat_stack[-1]
            if new_state == "normal":
                if current_state in self.IDENTITY_TASK_STATES:
                    while self.chat_stack and self.chat_stack[-1] in self.IDENTITY_TASK_STATES:
                        state_to_pop = self.chat_stack.pop()
                        if state_to_pop in self.state_prompts:
                            del self.state_prompts[state_to_pop]
                elif current_state in self.DISCOVER_TASK_STATES:
                    while self.chat_stack and self.chat_stack[-1] in self.DISCOVER_TASK_STATES:
                        state_to_pop = self.chat_stack.pop()
                        if state_to_pop in self.state_prompts:
                            del self.state_prompts[state_to_pop]
                elif current_state in self.EMAIL_TASK_STATES:
                    while self.chat_stack and self.chat_stack[-1] in self.EMAIL_TASK_STATES:
                        state_to_pop = self.chat_stack.pop()
                        if state_to_pop in self.state_prompts:
                            del self.state_prompts[state_to_pop]   
                elif len(self.chat_stack) > 1:
                    state_to_pop = self.chat_stack.pop()
                    if state_to_pop in self.state_prompts:
                            del self.state_prompts[state_to_pop]           
            elif new_state != current_state:
                self.chat_stack.append(new_state)
                if prompt_to_save:
                    self.state_prompts[new_state] = prompt_to_save
    
    def get_bot_response(self, query):
        current_state = self.chat_stack[-1]
        response = ""
        action_data = None
        prompt_to_save = None
        handled = False 

        if query.lower() == "cancel":
            if current_state in self.IDENTITY_TASK_STATES:
                while self.chat_stack and self.chat_stack[-1] in self.IDENTITY_TASK_STATES:
                    state_to_pop = self.chat_stack.pop()
                    if state_to_pop in self.state_prompts:
                        del self.state_prompts[state_to_pop]
                response = f"I've cancelled the identity task. We are now in the '{self.chat_stack[-1]}' state."
            elif current_state in self.DISCOVER_TASK_STATES:
                while self.chat_stack and self.chat_stack[-1] in self.DISCOVER_TASK_STATES:
                    state_to_pop = self.chat_stack.pop()
                    if state_to_pop in self.state_prompts:
                        del self.state_prompts[state_to_pop]
                response = f"I've cancelled the help task. We are now in the '{self.chat_stack[-1]}' state."
            elif current_state in self.EMAIL_TASK_STATES:
                while self.chat_stack and self.chat_stack[-1] in self.EMAIL_TASK_STATES:
                    state_to_pop = self.chat_stack.pop()
                    if state_to_pop in self.state_prompts:
                        del self.state_prompts[state_to_pop]
                response = f"I've cancelled the email task. We are now in the '{self.chat_stack[-1]}' state."
            elif len(self.chat_stack) > 1:
                state_to_pop = self.chat_stack.pop()
                if state_to_pop in self.state_prompts:
                        del self.state_prompts[state_to_pop]
                response = f"I've cancelled the ongoing task. We are now in the '{self.chat_stack[-1]}' state. What now?"
            else:
                response = "There is no ongoing task to cancel."
            self.add_chat_message(response, "bot")
            return
        elif query.lower() == "go back":
            if len(self.chat_stack) > 1:
                state_popped = self.chat_stack.pop()
                if state_popped in self.state_prompts:
                    del self.state_prompts[state_popped]
                response = f"Okay, I've gone back one step. We are now in the '{self.chat_stack[-1]}' state."
            else:
                response = "There's nothing to go back to."
            self.add_chat_message(response, "bot")
            return
        elif query.lower() == "where am i" or query.lower() == "where am i?":
            response = f"The chatbot is currently in the '{current_state}' state."
            self.add_chat_message(response, "bot")
            return
        elif query.lower() == "repeat":
            current_state = self.chat_stack[-1]
            if current_state == "normal":
                response = "There's no active task to repeat. How can I help?"
            elif current_state in self.state_prompts:
                response = self.state_prompts[current_state]
            else:
                response = f"I'm in the '{current_state}' state, but I don't have a specific prompt to repeat. What would you like to do?"
            self.add_chat_message(response, "bot")
            return
        elif query.lower() == "what now" or query.lower() == "what now?":
            current_state = self.chat_stack[-1]
            default_fallback = f"I'm in the '{current_state}' state. You can try 'cancel' to exit this task or 'go back' to the previous step."
            response = self.what_now_prompts.get(current_state, default_fallback)
            self.add_chat_message(response, "bot")
            return

        intent, subintent, score = self.intent_classifier.classify(query, threshold=0.2)
        
        if current_state in self.IDENTITY_TASK_STATES:
            handled = True
            response_text, new_name, new_state = self.identity_handler.get_identity_response(query, self.username, subintent="none", current_state=current_state)
            self.username = new_name
            prompt_to_save = response_text if new_state != "normal" else None
            self.manage_state(new_state, prompt_to_save)
            response = response_text
        elif current_state in self.DISCOVER_TASK_STATES:
            handled = True
            response_text, new_state = self.discoverability_handler.get_discoverability_response(query, subintent="none", current_state=current_state)
            prompt_to_save = response_text if new_state != "normal" else None
            self.manage_state(new_state, prompt_to_save)
            response = response_text
        elif intent == "Email" or current_state in self.EMAIL_TASK_STATES:
            pass_signal = "I'm not sure how to handle that email request."
            new_state, response_text, session_data, action_data = self.email_handler.handle_email_task(current_state, subintent, query, self.session_id)
            if response_text != pass_signal:
                handled = True
                if session_data is not None:
                    self.session_id, self.email_address = session_data
                managed_new_state = new_state if new_state else "normal"
                prompt_to_save = response_text if managed_new_state != "normal" else None
                self.manage_state(managed_new_state, prompt_to_save)
                response = response_text
                if action_data:
                    if action_data['action'] == 'view_email':
                        EmailViewer(self.root, action_data['data'])
            pass 
        if not handled and intent == "IdentityManagement":
            handled = True
            response_text, new_name, new_state = self.identity_handler.get_identity_response(query, self.username, subintent=subintent, current_state=current_state)
            self.username = new_name
            prompt_to_save = response_text if new_state != "normal" else None
            self.manage_state(new_state, prompt_to_save)
            response = response_text
        elif not handled and intent == "SmallTalk":
            handled = True
            raw_response = self.small_talk_handler.get_small_talk_response(query, threshold=0.4)
            if "{username}" in raw_response:
                name_to_insert = self.username if self.username else "friend"
                response = raw_response.replace("{username}", name_to_insert)
            else:
                response = raw_response
        elif not handled and intent == "QuestionAnswering":
            handled = True
            response = self.qa_handler.get_QA_response(query, threshold=0.65)
        elif not handled and intent == "Discoverability":
            handled = True
            response_text, new_state = self.discoverability_handler.get_discoverability_response(query, subintent=subintent, current_state=current_state)
            prompt_to_save = response_text if new_state != "normal" else None
            self.manage_state(new_state, prompt_to_save)
            response = response_text
        if not handled:
            if intent == "Unrecognized":
                response = "Forgive me, but I'm unable to recognize what you are saying."
            else:
                response = "[SYSTEM ERROR]: An internal classification error occurred."
        self.add_chat_message(response, "bot")

if __name__ == '__main__':
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()