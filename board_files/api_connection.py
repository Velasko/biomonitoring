import settings
import usocket

import drequests as requests

def connect(hostname):
    resp = requests.post(
        "{}/sensor/auth".format(hostname),
        json=settings.auth_keys,
        headers=requests.json_header
    )

    if resp.status_code == 200:
        token = resp.json()["token"]
        return token
    elif resp.status_code == 409:
        raise ValueError("Invalid authentication keys")
    else:
        raise Exception("Unknown server response")

class ApiStream():
    def __init__(self, host, port):
        self.sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.addr = (host, port)
    
    def __enter__(self):
        self.sock.connect(self.addr)
        return self.sock

    def __exit__(self, *args):
        self.sock.close()
        