"""
Redis Key Prefix Constants
"""
REDIS_AUTH_ATTEMPT_PREFIX = "nfc_attempt:"        # Stores NFC authentication attempt status
REDIS_AUTH_CODE_PREFIX = "auth_code:"             # Stores authorization codes
REDIS_REFRESH_TOKEN_PREFIX = "refresh_token:"     # Stores refresh tokens
REDIS_SESSION_UUID_MAP_PREFIX = "sess_uuid:"      # Maps OSPASS session ID -> User UUID (s_id -> uuid)
REDIS_UUID_SESSION_MAP_PREFIX = "uuid_sess:"      # Reverse mapping: User UUID -> OSPASS session ID (uuid -> s_id) - Optional tracking
