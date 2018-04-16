import hashlib

def hash(val):
        return int(hashlib.sha1(val.encode('utf-8')).hexdigest(), 16)  % 2**32
