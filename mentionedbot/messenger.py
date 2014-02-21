import time
import util


class MentionedBot:
    NAME = 'mentioned_bot'
    VERSION = 'dev'
    AUTHOR = '/u/w1ndwak3r'
    SOURCE_URL = 'https://github.com/windy1/MentionedBot'
    USER_AGENT = 'User-Agent: ' + NAME + '/' + VERSION + ' by ' + AUTHOR
    NOTIFICATION_BODY = ("You have been mentioned in a [comment](%s) by /u/%s.\n\n%s\n\nNote: Replying to this message "
                         "will not send a reply to the original comment.\n\n---\n\n^[[Stop receiving notifications]"
                         "(http://www.reddit.com/message/compose?to=" + NAME + "&subject=Press+send+to+stop+receiving+"
                         "notifications&message=ignore)] ^| ^[[Report an issue](http://www.reddit.com/message/compose/"
                         "?to=" + AUTHOR.replace('/u/', '') + "&subject=Issue+with+" + NAME + ")] "
                         "^| ^[[Source](" + SOURCE_URL + ")]")

    reddit = None

    def notify(self, redditor, comment):
        username = redditor.name

        # Make sure the user isn't in the blacklist
        blacklist = util.load_list(util.BLACKLIST_FILE, ',')
        if username in blacklist:
            print(username + " is blacklisted.")
            return

        permalink = comment.permalink
        quote = util.quote(comment.body)
        author = comment.author.name
        msg = self.NOTIFICATION_BODY % (permalink, author, quote)

        while msg.__len__() > 10000:                                                # Check message size
            quote_len = quote.__len__()                                             # Get the quote length
            quote = quote[:quote_len - 2]                                           # Chop off a character
            msg = self.NOTIFICATION_BODY % (permalink, author, quote)  # Reassign the message

        print('Sending message to ' + username + '...', end="")
        self.reddit.send_message(username, 'You have been mentioned in a comment.', msg)
        print('[DONE]')

    def start(self):
        self.reddit = util.login(self.USER_AGENT)
        already_done = []

        while True:

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

                        # Parse the possible username
                        username = util.parse_username(word[3:])
                        print("\nPossible match: '" + username + "'...", end="")

                        # Get the redditor
                        try:
                            redditor = self.reddit.get_redditor(username)
                        except Exception as e:
                            print(e)
                            continue

                        # Redditor is null
                        if redditor is None:
                            print('[NO MATCH]')
                            continue

                        # Username was valid
                        print('[MATCH FOUND]')

                        # Check to see if we've parsed this comment already
                        permalink = comment.permalink
                        if permalink in already_done:
                            break

                        # Notify the mentioned redditor
                        self.notify(redditor, comment)

                # permalink will not be None if a user was notified
                if permalink is not None:
                    already_done.append(permalink)

            # Wait 30 seconds
            print('')
            util.wait(30)


if __name__ == '__main__':
    MentionedBot().start()
