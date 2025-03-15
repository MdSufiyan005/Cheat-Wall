import random
import string
import base64
import json
import hashlib
import logging
import hmac
import sys
from functools import wraps
from datetime import datetime
from flask import abort, redirect, url_for, flash
from flask_login import current_user

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Simple encryption available everywhere without external dependencies
CRYPTO_AVAILABLE = True
logger.info("Encryption module initialized with CRYPTO_AVAILABLE = %s", CRYPTO_AVAILABLE)


def generate_access_code(length=6):
    """Generate a random alphanumeric access code for tests"""
    characters = string.ascii_uppercase + string.digits
    while True:
        # Generate a random code
        code = ''.join(random.choice(characters) for _ in range(length))
        # Ensure it doesn't look like offensive words
        if not any(bad_word in code.lower() for bad_word in ['ass', 'sex', 'fuk']):
            return code


def requires_roles(roles):
    """Decorator to restrict access based on user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def simple_encrypt(data_str, secret_key):
    """
    Simple encryption using XOR and base64.
    Not cryptographically secure but doesn't require external dependencies.
    """
    try:
        # Create a key from the secret
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        
        # XOR the data with the repeating key
        data_bytes = data_str.encode()
        encrypted = bytearray()
        
        for i in range(len(data_bytes)):
            encrypted.append(data_bytes[i] ^ key_bytes[i % len(key_bytes)])
        
        # Add a simple signature
        signature = hmac.new(key_bytes, data_bytes, hashlib.sha256).digest()[:8]
        final_bytes = signature + encrypted
        
        # Encode as base64
        return base64.urlsafe_b64encode(final_bytes).decode()
    except Exception as e:
        logger.error(f"Encryption error in simple_encrypt: {str(e)}")
        # Create a simple fallback code that isn't encrypted but at least contains the data
        try:
            # Just base64 encode the data with a simple prefix
            fallback = "UNENCRYPTED:" + base64.urlsafe_b64encode(data_str.encode()).decode()
            logger.warning(f"Using unencrypted fallback encoding")
            return fallback
        except:
            logger.error("Even fallback encoding failed")
            return None


def simple_decrypt(encrypted_str, secret_key):
    """
    Decrypt data encrypted with simple_encrypt.
    """
    try:
        # Check if this is an unencrypted fallback
        if encrypted_str.startswith("UNENCRYPTED:"):
            # Extract the base64 part
            base64_part = encrypted_str[12:]  # Skip "UNENCRYPTED:"
            # Decode base64 to get the original data
            return base64.urlsafe_b64decode(base64_part).decode()
            
        # Regular decryption
        # Decode base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_str)
        
        # Extract signature and encrypted data
        signature = encrypted_bytes[:8]
        encrypted_data = encrypted_bytes[8:]
        
        # Create key from secret
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        
        # XOR to decrypt
        decrypted = bytearray()
        for i in range(len(encrypted_data)):
            decrypted.append(encrypted_data[i] ^ key_bytes[i % len(key_bytes)])
        
        # Verify signature
        decrypted_str = decrypted.decode()
        verify_signature = hmac.new(key_bytes, decrypted_str.encode(), hashlib.sha256).digest()[:8]
        
        if not hmac.compare_digest(signature, verify_signature):
            logger.warning("Signature verification failed")
            return None
            
        return decrypted_str
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        return None


def encrypt_test_data(test_id, access_code, processes, start_time, end_time, secret_key):
    """
    Encrypt test data into a single code that can be distributed to students.
    
    Args:
        test_id: ID of the test
        access_code: Access code for the test
        processes: List of processes to be monitored
        start_time: Test start time (datetime object)
        end_time: Test end time (datetime object)
        secret_key: Secret key for encryption
        
    Returns:
        Encrypted code string or None if encryption failed
    """
    logger.debug(f"Encrypting test data with ID: {test_id}, code: {access_code}")
    logger.debug(f"Processes: {processes}")
    logger.debug(f"Start time: {start_time}, End time: {end_time}")
    
    try:
        # Convert datetime to ISO format for JSON serialization
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        # Create data payload
        data = {
            'test_id': test_id,
            'code': access_code,
            'processes': processes,
            'start': start_time_str,
            'end': end_time_str,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Created data payload: {data}")
        
        # Generate a verification hash
        verification = hashlib.sha256(json.dumps(data).encode()).hexdigest()[:10]
        data['verification'] = verification
        logger.debug(f"Added verification hash: {verification}")
        
        # Convert to JSON
        try:
            json_data = json.dumps(data)
            logger.debug(f"JSON serialization successful, length: {len(json_data)}")
        except Exception as json_error:
            logger.error(f"JSON serialization failed: {str(json_error)}")
            # Try to find problematic fields
            for key, value in data.items():
                try:
                    json.dumps({key: value})
                except Exception as field_error:
                    logger.error(f"Problem with field '{key}': {str(field_error)}")
            raise
        
        # Encrypt using our simple method
        encrypted_data = simple_encrypt(json_data, secret_key)
        if encrypted_data:
            logger.debug(f"Encryption successful, length: {len(encrypted_data)}")
        else:
            logger.error("Encryption returned None")
        
        return encrypted_data
    except Exception as e:
        import traceback
        logger.error(f"Failed to encrypt test data: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def decrypt_test_data(encrypted_code, secret_key):
    """
    Decrypt an encrypted test code.
    
    Args:
        encrypted_code: The encrypted code string
        secret_key: Secret key for decryption
        
    Returns:
        Decrypted test data as a dictionary or None if decryption failed
    """
    try:
        # Decrypt using our simple method
        json_data = simple_decrypt(encrypted_code, secret_key)
        if json_data is None:
            return None
            
        # Parse JSON
        data = json.loads(json_data)
        
        # Extract and verify hash
        verification = data.pop('verification')
        verification_check = hashlib.sha256(json.dumps(data).encode()).hexdigest()[:10]
        
        if verification != verification_check:
            logger.warning("Data verification failed, code may have been tampered with")
            return None
        
        # Convert ISO datetime strings back to datetime objects
        data['start'] = datetime.fromisoformat(data['start']) 
        data['end'] = datetime.fromisoformat(data['end'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return data
    except Exception as e:
        logger.error(f"Failed to decrypt code: {str(e)}")
        return None
