# pylint: disable=no-member
import sqlite3
import threading
import re
from functools import wraps
from PyQt5.QtWidgets import QMessageBox
from config.utils_constants import DATABASE_PATH

class DatabaseManager:
    """
    Singleton database manager class to handle connections and common operations
    """
    db_path = DATABASE_PATH
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.connection_pool = []
                cls._instance.max_connections = 5  # Maximum number of connections in the pool
            elif db_path and cls._instance.db_path != db_path:
                cls._instance.db_path = db_path
        return cls._instance
    
    def get_connection(self):
        """Get a connection from the pool or create a new one if needed"""
        if not self.connection_pool:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable row factory for named columns
            return conn
        else:
            return self.connection_pool.pop()
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        if len(self.connection_pool) < self.max_connections:
            self.connection_pool.append(conn)
        else:
            conn.close()

    def execute_query(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """
        Execute a query with error handling
        
        Args:
            query: SQL query string
            params: Parameters for the query
            fetchone: If True, fetch one result
            fetchall: If True, fetch all results
            commit: If True, commit changes
            
        Returns:
            Query results if fetchone or fetchall is True, otherwise None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            result = None
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            
            if commit:
                conn.commit()
                
            return result
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_transaction(self, queries):
        """
        Execute multiple queries in a transaction
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            conn.execute("BEGIN TRANSACTION")
            
            for query, params in queries:
                cursor.execute(query, params)
                
            conn.commit()
            return True
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

# Decorator for database operations with error handling
# In db_manager.py, modify the db_operation decorator:

def db_operation(error_message="Database operation failed"):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"❌ Error in {func.__name__}: {e}")
                if hasattr(self, 'parent') and self.parent():
                    QMessageBox.warning(self.parent(), "Database Error", f"{error_message}: {e}")
                else:
                    QMessageBox.warning(self, "Database Error", f"{error_message}: {e}")
                return None
        return wrapper
    return decorator


# Function to validate input data
def validate_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None if email else True

def validate_phone(phone):
    """Validate phone number format (07XXXXXXXX)"""
    pattern = r'^07\d{8}$'
    return re.match(pattern, phone) is not None if phone else True