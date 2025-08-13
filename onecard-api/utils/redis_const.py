"""
Redis Key Prefix Constants
"""
REDIS_AUTH_ATTEMPT_PREFIX = "nfc_attempt:"        # Stores NFC authentication attempt status
REDIS_AUTH_CODE_PREFIX = "auth_code:"             # Stores authorization codes
REDIS_REFRESH_TOKEN_PREFIX = "refresh_token:"     # Stores refresh tokens
REDIS_SESSION_PUB_MAP_PREFIX = "sess_pub:"      # Maps OSPASS session ID -> User Publickey (s_id -> pubkey)
REDIS_PUB_SESSION_MAP_PREFIX = "pub_sess:"      # Reverse mapping: User Publickey -> OSPASS session ID (pubkey -> s_id) - Optional tracking
