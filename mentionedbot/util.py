import string
import praw
import time

BLACKLIST_FILE = 'blacklist.txt'


def is_ignored(redditor):
    username = redditor.name.lower()
    # Make sure the user isn't in the blacklist
    blacklist = load_list(BLACKLIST_FILE, ',')
    if username in blacklist:
        print(username + " is blacklisted.")
        return True
    return False


def login(user_agent):
    while True:
        try:
            print(user_agent)
            r = praw.Reddit(user_agent)
            r.login()
            return r
        except praw.errors.InvalidUserPass:
            print('Invalid username or password.')


def load_list(file_name, delimiter):
    with open(file_name, 'r') as file:
        return file.read().split(delimiter)


def append_to_file(file_name, s):
    with open(file_name, 'a') as file:
        file.write(s)


def write_to_file(file_name, s):
    with open(file_name, 'w') as file:
        file.write(s)


def update(i):
    print('\rStarting in: [%d]' % i, end="")


def wait(secs):
    for i in range(secs, 0, -1):
        update(i)
        time.sleep(1)
    update(0)


def quote(body):
    body = body.strip().replace('&gt;', '>')
    new_body = ''
    for line in body.split('\n\n'):
        new_body += '>' + line + '\n\n'
    return new_body


def parse_username(s):
    for i in range(0, s.__len__()):
        ch = s[i]
        if ch in string.punctuation and ch is not '_':
            return s[:i]
    return s