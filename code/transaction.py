import re
import os
import random
from guerrilla_mail import GuerrillaSession
from requests.exceptions import RequestException, ConnectionError, HTTPError
from urllib3.exceptions import NameResolutionError

EMAIL_AWAITING_STATES = [
    'awaiting_session_start_confirm',
    'awaiting_session_restore_confirm',
    'awaiting_session_restore',
    'awaiting_session_end_confirm',
    'awaiting_view_index',
    'awaiting_delete_index',
    'awaiting_download_index',
    'awaiting_delete_all_confirm'
]
EMAIL_LOOP_STATES = ['email_manage_loop']

class EmailResponseGenerator:
    def __init__(self):
        self.templates = {
            'start_session': [
                "Great! Here is your info: \nTemporary Email: {email}\nSession ID: {sid}",
                "All set! Your new temporary email is {email} and the session ID is {sid}.",
                "Got it. I've created {email} for you. Your session ID is {sid}."
            ],
            'restore_session': [
                "Welcome back! Your session [{sid}] for [{email}] has been restored.",
                "Okay, I've loaded your session for {email}. Good to see you again!",
                "Session [{sid}] restored. Your email address is {email}."
            ],
            'list_emails': [
                "Here are your emails:\n{list_text}\nIf you'd like, you can view, download, or delete (multiple) emails."
            ],
            'delete_emails': [
                "Okay, {result_text}.",
                "Done. {result_text}.",
                "{result_text}."
            ],
            'download_emails': [
                "Got it. {result_text}.",
                "Successfully {result_text}.",
                "Task complete. {result_text}."
            ],
            'inbox_empty': [
                "Your inbox is currently empty.",
                "Looks like there's nothing here. Your inbox is empty.",
                "No emails found in your inbox."
            ],
            'manage_session': [
                "You have an active email session. You can 'list emails', 'view [index]', 'delete [index]', 'download [index]', or 'end session'.",
                "Okay, you're in your email session. What would you like to do? You can list, view, download, delete, or end the session.",
                "Session active. Your options are: list emails, view, download, delete, or end session."
            ],
            'confirm_delete_all': [
                "Are you absolutely sure you want to delete ALL emails in your inbox? This cannot be undone.",
                "Warning: This will permanently delete all messages. Are you sure you want to proceed?",
                "Just to confirm, you want to delete every single email? Please say 'yes' or 'no'."
            ]
        }

    def generate_response(self, content_data):
        intent_type = content_data.get('type')
        if intent_type == 'start_session':
            template = random.choice(self.templates['start_session'])
            return template.format(email=content_data['email'], sid=content_data['sid'])
        elif intent_type == 'restore_session':
            template = random.choice(self.templates['restore_session'])
            return template.format(email=content_data['email'], sid=content_data['sid'])
        elif intent_type == 'list_emails':
            inbox = content_data.get('inbox', [])
            if not inbox:
                return random.choice(self.templates['inbox_empty'])
            list_text = ""
            for i, email in enumerate(inbox, 1):
                list_text += f"  {i}. From: {email['mail_from']}, Subject: {email['mail_subject']}\n"
            template = random.choice(self.templates['list_emails'])
            return template.format(list_text=list_text.rstrip())
        elif intent_type == 'delete_emails':
            template = random.choice(self.templates['delete_emails'])
            return template.format(result_text=content_data['result_text'])
        elif intent_type == 'download_emails':
            template = random.choice(self.templates['download_emails'])
            return template.format(result_text=content_data['result_text'])
        elif intent_type == 'manage_session':
            return random.choice(self.templates['manage_session'])
        elif intent_type == 'confirm_delete_all':
            return random.choice(self.templates['confirm_delete_all'])
        return "I'm not sure how to phrase that."

class EmailHandler:
    def __init__(self):
        self.responder = EmailResponseGenerator()

    def _extract_session_id(self, text):
        match = re.search(r'\b([a-z0-9]{26})\b', text.lower())
        return match.group(1) if match else None

    def _extract_email_id(self, text):
        match = re.search(r'\b(\d+)\b', text.lower())
        return match.group(1) if match else None

    def _extract_email_indices(self, text, subintent):
        processed_text = text.lower().replace(subintent, "").strip()
        if "all" in processed_text:
            return "all"
        matches = re.findall(r'(\d+-\d+|\d+)', processed_text)  
        if matches:
            return ",".join(matches)
        return None
        
    def _get_mail_id_from_index(self, session, index_str):
        if not session.inbox:
            session.get_inbox_list()
        if index_str.isdigit():
            try:
                list_index = int(index_str) - 1
                if 0 <= list_index < len(session.inbox):
                    return session.inbox[list_index]['mail_id']
            except:
                pass 
        return index_str

    def handle_email_task(self, current_state, subintent, user_input, session_id):
        response = "I'm not sure how to handle that email request."
        new_state = current_state
        new_session_data = None
        action_data = None
        try:
            management_intents = ['list_emails', 'update_inbox', 'view_email', 'download_email','delete_email', 'end_session', 'manage_session', 'exit_loop']
            if not session_id and subintent in management_intents:
                response = "You don't have an active temporary email session. Would you like to create one?"
                new_state = 'awaiting_session_start_confirm'
                return (new_state, response, None, None)
            
            if subintent == 'start_session':
                if session_id:
                    response = "You already have an active session. You must 'end session' before starting a new one."
                    new_state = None
                    return (new_state, response, None, None)
                session = GuerrillaSession()
                success = session.start_new_session()
                if success:
                    new_session_id = session.sid_token
                    new_email_address = session.email_addr
                    content = {'type': 'start_session', 'email': new_email_address, 'sid': new_session_id}
                    response = self.responder.generate_response(content)
                    new_state = None 
                    new_session_data = (new_session_id, new_email_address)
                else:
                    response = "Error: Could not start a new session. The mail server might be down."
                    new_state = None
                return (new_state, response, new_session_data, None)
            elif subintent == 'restore_session':
                provided_id = self._extract_session_id(user_input)
                if provided_id:
                    session = GuerrillaSession()
                    success = session.restore_session(sid_token=provided_id)
                    if success:
                        email_address = session.email_addr
                        content = {'type': 'restore_session', 'email': email_address, 'sid': provided_id}
                        response = self.responder.generate_response(content)                      
                        new_state = None 
                        new_session_data = (provided_id, email_address)
                    else:
                        response = "Error: Could not restore session."
                        new_state = 'awaiting_session_restore_confirm'
                else:
                    response = "Okay, I can help with that. What is your session ID?"
                    new_state = 'awaiting_session_restore'
                return (new_state, response, new_session_data, None)
            elif subintent == 'end_session' and session_id:
                response = "Are you sure you want to end your current session? This will permanently delete your temporary email address."
                new_state = 'awaiting_session_end_confirm'
                return (new_state, response, None, None)
            
            if current_state == 'awaiting_session_start_confirm':
                if 'yes' in user_input.lower():
                    return self.handle_email_task(None, 'start_session', user_input, None)
                else:
                    response = "Okay, no problem. Let me know if you change your mind."
                    new_state = None
                return (new_state, response, None, None)
            elif current_state == 'awaiting_session_restore':
                provided_id = self._extract_session_id(user_input)
                if provided_id:
                    return self.handle_email_task(None, 'restore_session', user_input, None)
                else:
                    response = "I didn't catch a session ID in that message. Please provide your full session ID, or say 'cancel'."
                return (new_state, response, None, None)
            elif current_state == 'awaiting_session_restore_confirm':
                if 'no' in user_input.lower() or 'cancel' in user_input.lower():
                    response = "Okay, cancelling session restore."
                    new_state = None 
                    return (new_state, response, None, None)
                provided_id = self._extract_session_id(user_input)
                if provided_id:
                    return self.handle_email_task(None, 'restore_session', user_input, None)
                else:
                    response = "Okay, what is the session ID you'd like to try?"
                    new_state = 'awaiting_session_restore' 
                return (new_state, response, None, None)
            elif current_state == 'awaiting_session_end_confirm':
                if 'yes' in user_input.lower():
                    session = GuerrillaSession()
                    session.restore_session(sid_token=session_id)
                    success = session.forget_current_email()
                    if success:
                        response = "Your session has been ended and your email address deleted. Let me know if you need a new one."
                        new_session_data = (None, None) 
                    else:
                        response = "Sorry, I had trouble ending the session. Please try again."
                    new_state = None
                else:
                    response = "Okay, I won't end your session. What's next?"
                    new_state = None
                return (new_state, response, new_session_data, None)
            elif current_state == 'awaiting_view_index':
                email_index_str = self._extract_email_id(user_input)
                if email_index_str:
                    return self.handle_email_task('email_manage_loop', 'view_email', user_input, session_id)
                else:
                    response = "I didn't catch that. Please provide a number for the email you want to view, or say 'cancel'."
                    new_state = 'awaiting_view_index'
                return (new_state, response, None, None) 
            elif current_state == 'awaiting_download_index':
                indices_str = self._extract_email_indices(user_input, "download")
                if indices_str:
                    return self.handle_email_task('email_manage_loop', 'download_email', user_input, session_id)
                else:
                    response = "I didn't catch that. Please provide indices (e.g., '1', '1, 2', '1-3', 'all'), or say 'cancel'."
                    new_state = 'awaiting_download_index'
                return (new_state, response, None, None)
            elif current_state == 'awaiting_delete_index':
                indices_str = self._extract_email_indices(user_input, "delete")
                if indices_str:
                    if indices_str.strip() == 'all':
                        response = self.responder.generate_response({'type': 'confirm_delete_all'})
                        new_state = 'awaiting_delete_all_confirm'
                    else:
                        return self.handle_email_task('email_manage_loop', 'delete_email', user_input, session_id)
                else:
                    response = "I didn't catch that. Please provide indices (e.g., '1', '1, 2', '1-3', 'all'), or say 'cancel'."
                    new_state = 'awaiting_delete_index'
                return (new_state, response, None, None)
            elif current_state == 'awaiting_delete_all_confirm':
                if 'yes' in user_input.lower():
                    session = GuerrillaSession()
                    session.restore_session(sid_token=session_id)
                    session.get_inbox_list() 
                    deleted_ids = session.delete_emails('all')
                    if deleted_ids is not None:
                        result_text = f"Successfully deleted {len(deleted_ids)} email(s)."
                        response = self.responder.generate_response({'type': 'delete_emails', 'result_text': result_text})
                    else:
                        response = "Sorry, I failed to delete those emails. (Did you already delete them?)"
                    new_state = 'email_manage_loop'
                else:
                    response = "Okay, I've cancelled the deletion."
                    new_state = 'email_manage_loop'
                return (new_state, response, None, None)
            
            if session_id:
                session = GuerrillaSession()
                session.restore_session(sid_token=session_id) 
                if not session.email_addr:
                    raise Exception("Session expired or is invalid.")
                if subintent == 'exit_loop':
                    response = "Okay, closing the email task. I'll remember your session if you need it again."
                    new_state = None
                    return (new_state, response, None, None)
                if subintent in ['view_email', 'download_email', 'delete_email']:
                    session.get_inbox_list()
                if subintent in ['list_emails', 'update_inbox']:
                    inbox = session.get_inbox_list()
                    response = self.responder.generate_response({'type': 'list_emails', 'inbox': inbox})
                    new_state = 'email_manage_loop'
                elif subintent == 'view_email':
                    email_index_str = self._extract_email_id(user_input)
                    if email_index_str:
                        email_content = session.fetch_email_body(email_index_str)
                        if isinstance(email_content, dict) and 'mail_body' in email_content:
                            subject = email_content.get('mail_subject', 'No Subject')
                            response = f"Opening email {email_index_str}: '{subject}'"
                            action_data = {'action': 'view_email', 'data': email_content}
                        else:
                            response = f"Error: Could not fetch email index {email_index_str}."
                            new_state = 'email_manage_loop'
                    else:
                        response = "Which email index would you like to view? Please enter a number."
                        new_state = 'awaiting_view_index'
                elif subintent == 'download_email':
                    indices_str = self._extract_email_indices(user_input, subintent)
                    if indices_str:
                        (downloaded_files, failed_files) = session.download_emails(indices_str)
                        result_text = f"Successfully downloaded {len(downloaded_files)} email(s)."
                        if failed_files > 0:
                            result_text += f" {failed_files} failed."
                        response = self.responder.generate_response({'type': 'download_emails', 'result_text': result_text})
                        new_state = 'email_manage_loop'
                    else:
                        response = "Which email(s) would you like to download? You can enter '1', '1, 2', '1-3', or 'all'."
                        new_state = 'awaiting_download_index'
                elif subintent == 'delete_email':
                    indices_str = self._extract_email_indices(user_input, subintent)
                    if indices_str:
                        if indices_str.strip() == 'all':
                            response = self.responder.generate_response({'type': 'confirm_delete_all'})
                            new_state = 'awaiting_delete_all_confirm'
                        else:
                            deleted_ids = session.delete_emails(indices_str)
                            if deleted_ids is not None:
                                result_text = f"Successfully deleted {len(deleted_ids)} email(s)."
                            else:
                                result_text = "I failed to delete those emails."
                            response = self.responder.generate_response({'type': 'delete_emails', 'result_text': result_text})
                            new_state = 'email_manage_loop'
                    else:
                        response = "Which email(s) would you like to delete? You can enter '1', '1, 2', '1-3', or 'all'."
                        new_state = 'awaiting_delete_index'
                elif subintent == 'end_session':
                    response = "Are you sure you want to end your current session?"
                    new_state = 'awaiting_session_end_confirm'
                elif subintent == 'manage_session':
                    response = self.responder.generate_response({'type': 'manage_session'})
                    new_state = 'email_manage_loop'
                else: 
                    #response = self.responder.generate_response({'type': 'manage_session'})
                    #new_state = 'email_manage_loop'
                    pass # Should pass down now
                return (new_state, response, new_session_data, action_data)
            pass

        except (ConnectionError, NameResolutionError) as e:
            print(f"[TRANSACTION_ERROR] Connection error: {e}")
            response = "I'm sorry, I'm having trouble connecting to the email service. Please check your internet connection and try again."
            new_state = None
        except (RequestException, HTTPError) as e:
            print(f"[TRANSACTION_ERROR] API error: {e}")
            response = "The email service seems to be down or experiencing issues. Please try again in a moment."
            new_state = None
        except ValueError as e:
            print(f"[TRANSACTION_ERROR] Value error: {e}")
            response = f"I ran into a value error, did you put in a valid email number? Please double check your inbox and try again."
            new_state = current_state
        except Exception as e:
            print(f"[TRANSACTION_ERROR] An unexpected error occurred: {e}")
            response = f"An unexpected error occurred: {e}. Returning to the main menu."
            new_state = None
        return (new_state, response, new_session_data, action_data)