import requests
import time
import os
import json
from requests.exceptions import RequestException, HTTPError, ConnectionError
from urllib3.exceptions import NameResolutionError

# This is the API implementation
class GuerrillaSession:
    
    API_URL = "https://api.guerrillamail.com/ajax.php"

    def __init__(self, lang='en'):
        self.session = requests.Session()
        self.lang = lang
        self.sid_token = None
        self.email_addr = None
        self.email_timestamp = None
        self.alias = None
        self.inbox = []
        
    def start_new_session(self):
        params = {'lang': self.lang}
        self.sid_token = None 
        response = self._api_call('get_email_address', params, method='GET')
        if response and 'email_addr' in response:
            self._update_session_details(response)
            return True
        return False

    def restore_session(self, sid_token):
        if not sid_token:
            raise ValueError("Session ID is required to restore.")
            
        params = {'sid_token': sid_token, 'lang': self.lang}
        response = self._api_call('get_email_address', params, method='GET')
        
        if response and 'auth' in response and 'error_codes' in response['auth'] and 'auth-session-not-initialized' in response['auth']['error_codes']:
            raise Exception(f"Session ID {sid_token} is invalid or has expired.")
        elif response and 'email_addr' in response:
            self._update_session_details(response)
            return True
        return False

    def _update_session_details(self, response_json):
        if not isinstance(response_json, dict):
            return

        self.sid_token = response_json.get('sid_token', self.sid_token)
        self.email_addr = response_json.get('email_addr', self.email_addr)
        self.email_timestamp = response_json.get('email_timestamp', self.email_timestamp)
        self.alias = response_json.get('alias', self.alias)
        
        if 'list' in response_json:
            existing_ids = {email['mail_id'] for email in self.inbox}
            new_emails = [email for email in response_json['list'] if email['mail_id'] not in existing_ids]
            self.inbox = new_emails + self.inbox
            self.inbox.sort(key=lambda x: int(x.get('mail_timestamp', 0)), reverse=True)

    def _api_call(self, func_name, params=None, method='GET'):
        if params is None:
            params = {}
        if isinstance(params, dict):
            params_list = list(params.items())
        else:
            params_list = list(params) 
        if 'f' not in [p[0] for p in params_list]:
            params_list.append(('f', func_name))
        if self.sid_token and 'sid_token' not in [p[0] for p in params_list]:
            params_list.append(('sid_token', self.sid_token))

        try:
            if method.upper() == 'GET':
                response = self.session.get(self.API_URL, params=params_list, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(self.API_URL, data=params_list, timeout=10)
            else:
                raise ValueError("Method must be 'GET' or 'POST'")

            response.raise_for_status()
            response_json = response.json()

            if not isinstance(response_json, dict):
                return response_json
            
            if 'sid_token' in response_json and response_json['sid_token'] != self.sid_token:
                self.sid_token = response_json['sid_token']
            
            self._update_session_details(response_json)
            return response_json

        except (ConnectionError, NameResolutionError, HTTPError, RequestException) as e:
            print(f"[GuerrillaSession ERROR] API call failed: {e}")
            raise e
        except json.JSONDecodeError:
            print(f"[GuerrillaSession ERROR] Failed to decode JSON response: {response.text}")
            raise Exception("Failed to decode API response.")
        return None 

    def get_inbox_list(self, offset=0):
        if not self.sid_token:
            raise Exception("No active session.")
        response = self._api_call('get_email_list', {'offset': str(offset)})
        if response and 'list' in response:
            return self.inbox
        return []

    def _get_email_ids_from_indices(self, indices_str):
        if not self.inbox:
            return []
            
        indices_to_process = set()
        max_index = len(self.inbox)
        
        if indices_str.lower() == 'all':
            return [email['mail_id'] for email in self.inbox]
            
        parts = indices_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start < 1: start = 1
                    if end > max_index: end = max_index
                    indices_to_process.update(range(start - 1, end))
                except ValueError:
                    continue
            else:
                try:
                    index = int(part)
                    if 1 <= index <= max_index:
                        indices_to_process.add(index - 1)
                except ValueError:
                    continue
                    
        mail_ids = [self.inbox[i]['mail_id'] for i in sorted(list(indices_to_process))]
        return mail_ids

    def fetch_email_body(self, index):
        if not self.sid_token:
            raise Exception("No active session.")
        try:
            index_int = int(index)
            if not (1 <= index_int <= len(self.inbox)):
                raise ValueError(f"Index {index_int} is out of bounds (1-{len(self.inbox)}).")
        except ValueError:
            raise ValueError("Index must be a number.")
            
        mail_id = self.inbox[index_int - 1]['mail_id']
        response = self._api_call('fetch_email', {'email_id': mail_id})
        
        if response and 'mail_body' in response:
            self.inbox[index_int - 1]['mail_read'] = '1'
            return response
        return None

    def delete_emails(self, indices_str):
        if not self.sid_token:
            raise Exception("No active session.")
        
        mail_ids = self._get_email_ids_from_indices(indices_str)
        if not mail_ids:
            raise ValueError("No valid email indices provided.")
            
        params = [('email_ids[]', mid) for mid in mail_ids]
        response = self._api_call('del_email', params=params, method='POST')
        
        if response and 'deleted_ids' in response:
            deleted_ids_set = set(response['deleted_ids'])
            self.inbox = [email for email in self.inbox if email['mail_id'] not in deleted_ids_set]
            return deleted_ids_set
        return None

    def download_emails(self, indices_str):
        if not self.sid_token:
            raise Exception("No active session.")
        
        mail_ids = self._get_email_ids_from_indices(indices_str)
        if not mail_ids:
            raise ValueError("No valid email indices provided.")
            
        save_dir = os.path.join("downloads", self.sid_token)
        os.makedirs(save_dir, exist_ok=True)
        
        downloaded_files = []
        failed_files = 0
        
        for mail_id in mail_ids:
            index = next((i for i, email in enumerate(self.inbox) if email['mail_id'] == mail_id), -1)
            if index == -1:
                failed_files += 1
                continue

            email_data = self.fetch_email_body(index + 1)
            
            if isinstance(email_data, dict) and 'mail_body' in email_data:
                subject = email_data.get('mail_subject', 'no_subject').replace(' ', '_')
                subject = "".join(c for c in subject if c.isalnum() or c in ('_', '-')).rstrip()
                filename = f"{mail_id}_{subject[:30]}.html"
                filepath = os.path.join(save_dir, filename)   
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(email_data['mail_body'])
                    downloaded_files.append(filepath)
                except IOError as e:
                    print(f"Error writing file {filepath}: {e}")
                    failed_files += 1
            else:
                failed_files += 1
        return (downloaded_files, failed_files)

    def forget_current_email(self):
        if not self.sid_token:
            raise Exception("No active session.")
        if not self.email_addr:
            return True 
         
        params = {'email_addr': self.email_addr}
        response = self._api_call('forget_me', params, method='POST')
        
        if response:
            self.email_addr = None
            self.email_timestamp = None
            self.alias = None
            self.inbox = []
            return True
        return False