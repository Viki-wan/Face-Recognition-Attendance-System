import time
import json
import os

class LoginAttemptTracker:
    def __init__(self, cache_file='login_attempts.json'):
        self.cache_file = os.path.join(os.path.dirname(__file__), cache_file)
        self.login_attempts = self.load_attempts()

    def load_attempts(self):
        """Load login attempts from file, removing expired attempts."""
        try:
            if not os.path.exists(self.cache_file):
                return {}
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                attempts = json.load(f)
            
            # Remove expired attempts
            current_time = time.time()
            filtered_attempts = {
                username: (count, timestamp) 
                for username, (count, timestamp) in attempts.items() 
                if current_time - timestamp < 300  # 5 minutes
            }
            
            # Save filtered attempts back to file
            with open(self.cache_file, 'w') as f:
                json.dump(filtered_attempts, f)
            
            return filtered_attempts
        except (json.JSONDecodeError, IOError):
            return {}

    def record_failed_attempt(self, username):
        """Record a failed login attempt."""
        current_time = time.time()
        
        if username in self.login_attempts:
            attempts, _ = self.login_attempts[username]
            self.login_attempts[username] = (attempts + 1, current_time)
        else:
            self.login_attempts[username] = (1, current_time)
        
        # Save to file
        self._save_attempts()
        
        return self.login_attempts[username]

    def is_locked_out(self, username):
        """Check if the username is locked out."""
        current_time = time.time()
        
        if username not in self.login_attempts:
            return False
        
        attempts, last_attempt_time = self.login_attempts[username]
        
        # Check if more than 3 attempts within 5 minutes
        if attempts >= 3 and (current_time - last_attempt_time) < 300:
            return True
        
        return False

    def get_remaining_lockout_time(self, username):
        """Calculate remaining lockout time."""
        current_time = time.time()
        
        if username not in self.login_attempts:
            return 0
        
        attempts, last_attempt_time = self.login_attempts[username]
        remaining_time = int(300 - (current_time - last_attempt_time))
        
        return max(0, remaining_time)

    def reset_attempts(self, username):
        """Reset login attempts for a username."""
        if username in self.login_attempts:
            del self.login_attempts[username]
            self._save_attempts()

    def _save_attempts(self):
        """Save login attempts to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.login_attempts, f)
        except IOError:
            print("Warning: Could not save login attempts")