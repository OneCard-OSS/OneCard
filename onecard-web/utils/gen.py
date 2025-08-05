import string
import random

def gen_client_id():
    client_id = string.ascii_letters + string.digits
    return f"onecard-{''.join(random.choices(client_id, k=23)).lower()}"

def gen_client_secret():
    client_secret = hex(random.getrandbits(128))[2:]
    return client_secret