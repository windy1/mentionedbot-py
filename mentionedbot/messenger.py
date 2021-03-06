import time
import util
import argparse
import pymysql
import configparser


class MentionedBot:
    """
    Base class for mentionedbot defines the basic life cycle for implementations
    """

    # Constants
    NAME = 'mentionedbot3'
    VERSION = 'dev'
    AUTHOR = '/u/w1ndwak3r'
    SOURCE_URL = 'https://github.com/windy1/mentionedbot-py'
    USER_AGENT = 'User-Agent: ' + NAME + '/' + VERSION + ' by ' + AUTHOR
    NOTIFICATION_BODY = ("You have been mentioned in a [%s](%s) by /u/%s.\n\n%s\n\nNote: Replying to this message "
                         "will not send a reply to the original post.\n\n---\n\n^[[Stop receiving notifications]"
                         "(http://www.reddit.com/message/compose?to=" + NAME + "&subject=Press+send+to+stop+receiving+"
                         "notifications&message=ignore)] ^| ^[[Report an issue](http://www.reddit.com/message/compose/"
                         "?to=" + AUTHOR.replace('/u/', '') + "&subject=Issue+with+" + NAME + ")] "
                         "^| ^[[Source](" + SOURCE_URL + ")]")

    reddit = None
    start_time = 0
    already_done = []

    CONFIG_FILE = 'config.ini'

    # mysql
    db_cur = None
    db_conn = None
    host = None
    port = None
    db = None
    user = None
    passwd = None
    table = None

    def __init__(self, running_time_file, quiet=True, log=True):
        """
        Initializes the bot. Running time file defines where to store the running time of the bot. Quiet disables
        notifications when a redditor is mentioned. Log defines if mentions should be logged to a MySQL database.
        """
        self.running_time_file = running_time_file
        self.quiet = quiet
        self.log = log

    def get_running_time(self):
        """
        Returns the total running time this bot has run
        """
        with open(self.running_time_file, 'r') as file:
            return int(file.read().strip())

    def set_running_time(self, t):
        """
        Sets the total running time this bot has run
        """
        util.write_to_file(self.running_time_file, str(int(t)))

    def hello(self):
        """
        Prints a welcome message for the bot.
        """
        print(self.NAME + ' v' + self.VERSION + ' by ' + self.AUTHOR + ' started.')
        print('Source: ' + self.SOURCE_URL)
        if self.quiet:
            print('----- QUIET MODE ENABLED -----')
        if self.log:
            print('-----  LOGGING ENABLED   -----')
            self.connect_to_db()

    def read_config(self):
        """
        Initializes MySQL values from the config
        """
        print('Reading config...', end="")
        config = configparser.ConfigParser()
        config.read(self.CONFIG_FILE)
        mysql = config['mysql']
        self.host = mysql['host']
        self.port = int(mysql['port'])
        self.db = mysql['db']
        self.user = mysql['user']
        self.passwd = mysql['pass']
        self.passwd = None if self.passwd is 'None' else self.passwd
        self.table = mysql['table']
        print('[DONE]')

    def connect_to_db(self):
        """
        Connects to the configured MySQL database.
        """
        self.read_config()
        print('Connecting to database...', end="")
        self.db_conn = pymysql.connect(host=self.host, user=self.user, db=self.db)
        self.db_cur = self.db_conn.cursor()
        print('[DONE]')

    def disconnect_from_db(self):
        """
        Disconnects from the MySQL database
        """
        self.db_cur.close()
        self.db_conn.close()

    def record_mention(self, user, field):
        """
        Records a mention in the MySQL database. This will not run if log is false.
        """
        if not self.log:
            return

        print('Recording mention...', end="")
        user = user.lower()
        results = self.db_cur.execute("SELECT * FROM %s WHERE user = '%s'" % (self.table, user))
        if results == 0:
            # Create the user column if they haven't been previously mentioned
            stmt = "INSERT INTO %s VALUES ('%s', 0, 0, 0)" % (self.table, user)
            self.db_cur.execute(stmt)
            self.db_conn.commit()

        # Increment the proper field
        stmt = "UPDATE %s SET mentions_%s = mentions_%s + 1 WHERE user = '%s'" % (self.table, field, field, user)
        self.db_cur.execute(stmt)
        self.db_conn.commit()
        print('[DONE]')

    def parse_redditor(self, word):
        """
        Takes a word that must start with /u/ and attempts to return a Redditor object from it
        """
        # Parse the possible username
        username = util.parse_username(word[3:])
        print("\nPossible match: '" + username + "'...", end="")

        # Get the redditor
        try:
            redditor = self.reddit.get_redditor(username)
        except Exception as e:
            print(e)
            return None

        # Username was valid
        print('[MATCH FOUND]')
        return redditor

    def notify(self, thing, redditor, link, body, author):
        """
        Notifies the specified redditor that they have been mentioned.
        """
        if self.quiet or util.is_ignored(redditor):
            return

        quote = util.quote(body)
        msg = self.NOTIFICATION_BODY % (thing, link, author, quote)

        while msg.__len__() > 10000:                                   # Check message size
            quote_len = quote.__len__()                                # Get the quote length
            quote = quote[:quote_len - 2]                              # Chop off a character
            msg = self.NOTIFICATION_BODY % (permalink, author, quote)  # Reassign the message

        username = redditor.name
        print('Sending message to ' + username + '...', end="")
        self.reddit.send_message(username, 'You have been mentioned in a comment.', msg)
        print('[DONE]')

    def print_time(self):
        """
        Prints the current running time as well as the total running time.
        """
        now = time.time()
        running_time = now - self.start_time
        print('\nCurrent session running time: ' + str(running_time) + 's')

        total = self.get_running_time() + running_time
        print('Total running time: ' + str(total) + 's')
        self.set_running_time(total)

    def login(self, auth=True):
        """
        Logs into reddit
        """
        self.hello()
        self.reddit = util.login(self.USER_AGENT, auth)

    def tick(self):
        """
        An empty definition for implementations to handle every loop cycle
        """
        pass

    def start(self):
        """
        Logs in and starts the bot.
        """
        self.login(not self.quiet)
        self.start_time = time.time()
        while True:
            self.print_time()
            try:
                self.tick()
            except Exception as e:
                print(e)


class CommentMentionedBot(MentionedBot):
    def __init__(self, quiet=True, log=True):
        super().__init__('comments_time.txt', quiet, log)

    def tick(self):
        """
        Reads up to 1000 new comments from /r/all/.
        """

        # Get new comments from /r/all
        print('\n\nRetrieving comments...', end="")
        comments = list(self.reddit.get_comments('all', limit=None))
        print('[DONE]')

        comment_count = comments.__len__()
        print('Comments to read: ' + str(comment_count))
        for i in range(0, comment_count):
            comment = comments[i]

            # Update percent counter
            pcent = i / float(comment_count) * 100
            print('\rReading comments: [%d%%]' % pcent, end="")
            time.sleep(0.1)

            # Parse words
            words = comment.body.split()
            permalink = None
            for word in words:
                if word.startswith('/u/'):

                    # Get the redditor
                    redditor = self.parse_redditor(word)
                    if redditor is None:
                        continue

                    # Check to see if we've parsed this comment already
                    permalink = comment.permalink
                    if permalink in self.already_done:
                        print('Comment was already read.')
                        break

                    # Notify the mentioned redditor
                    self.notify('comment', redditor, permalink, comment.body, comment.author.name)
                    self.record_mention(redditor.name, 'comment')

            # permalink will not be None if a user was notified
            if permalink is not None:
                self.already_done.append(permalink)

        # Wait 30 seconds
        print('')
        util.wait(30)


class SubmissionMentionedBot(MentionedBot):
    def __init__(self, quiet=True, log=True):
        super().__init__('submissions_time.txt', quiet, log)

    def tick(self):
        """
        Reads submissions from reddit.com/new and check the title and self text for user names.
        """

        # Get new submissions
        print('\n\nRetrieve submissions...', end="")
        submissions = list(self.reddit.get_new(limit=None))
        print('[DONE]')

        submission_count = submissions.__len__()
        print('Submissions to read: ' + str(submission_count))
        for i in range(0, submission_count):
            submission = submissions[i]

            # Update percent counter
            pcent = i / float(submission_count) * 100
            print('\rReading submissions: [%d%%]' % pcent, end="")
            time.sleep(0.1)

            # Check title
            title = submission.title
            words = title.split()
            sub_id = None
            for word in words:
                if word.startswith('/u/'):

                    # Get the redditor
                    redditor = self.parse_redditor(word)
                    if redditor is None:
                        continue

                    # Check to see if we have parsed this submission already
                    sub_id = submission.id
                    if sub_id in self.already_done:
                        print('Submission was already read.')
                        break

                    # notify the redditor
                    author = submission.author
                    if author is None:
                        author = '[deleted]'
                    else:
                        author = author.name

                    self.notify('submission title', redditor, submission.short_link, title, author)
                    self.record_mention(redditor.name, 'title')

            # check self text
            body = submission.selftext
            words = body.split()
            for word in words:
                if word.startswith('/u/'):

                    # Get the redditor
                    redditor = self.parse_redditor(word)
                    if redditor is None:
                        continue

                    # Check to see if we have parsed this submission already
                    sub_id = submission.id
                    if sub_id in self.already_done:
                        print('Submission was already read.')
                        break

                    # notify the redditor
                    self.notify('submission', redditor, submission.short_link, body, submission.author.name)
                    self.record_mention(redditor.name, 'selftext')

            if sub_id is not None:
                self.already_done.append(sub_id)

        print('')
        util.wait(30)


def main():
    parser = argparse.ArgumentParser(description='Reddit bot for sending notifications to mentioned users.')
    parser.add_argument('-c', '--comments', help='Read comments', required=False, action='store_true')
    parser.add_argument('-s', '--submissions', help='Read submissions', required=False, action='store_true')
    parser.add_argument('-q', '--quiet', help='Do not notify the mentioned redditors', required=False,
                        action='store_true')
    parser.add_argument('-l', '--log', help='Logs the mentions.', required=False, action='store_true')
    args = parser.parse_args()

    if args.comments:
        CommentMentionedBot(quiet=args.quiet, log=args.log).start()
    elif args.submissions:
        SubmissionMentionedBot(quiet=args.quiet, log=args.log).start()
    else:
        print('Provide either -c or -s')


if __name__ == '__main__':
    main()
