import uuid
import hashlib
from dboj_site import settings, contests

def cmpProblem(a, b):
    if a[0] < b[0]:
        return -1
    elif a[0] > b[0]:
        return 1
    else:
        return a[1] - b[1]

def check_equal(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

def getLen(settings, contest):
    return settings.find_one({"type":"contest", "name":contest})['len']

def get_bonus(rem, pts):
    return (pts * rem) // 30000

def perms(found, author):
    acc = settings.find_one({"type":"access", "mode":found['contest'], "name":author})
    if (not settings.find_one({"type":"access", "mode":"owner", "name":author}) is None):
        return False # Has owner perms
    if (not settings.find_one({"type":"access", "mode":"admin", "name":author}) is None) and (author in found['authors']):
        return False # Has admin perms
    elif (not acc is None) and (found['status'] == "s") and contests.compare(acc['start'], contests.current_time()) <= getLen(settings, found['contest']):
        return False # Has contest participant perms
    return (not found['published']) or (found['status'] != "s")