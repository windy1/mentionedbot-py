import time
import util
import argparse


class MentionedBot:
    NAME = 'mentioned_bot'
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

        if util.is_ignored(redditor):
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

    def start(self):
        self.reddit = util.login(self.USER_AGENT)


class CommentMentionedBot(MentionedBot):
    def start(self):
        """
        Reads up to 1000 new comments from /r/all/.
        """

        super().start()
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

                        # Get the redditor
                        redditor = self.parse_redditor(word)
                        if redditor is None:
                            continue

                        # Check to see if we've parsed this comment already
                        permalink = comment.permalink
                        if permalink in already_done:
                            print('Comment was already read.')
                            break

                        # Notify the mentioned redditor
                        self.notify('comment', redditor, permalink, comment.body, comment.author.name)

                # permalink will not be None if a user was notified
                if permalink is not None:
                    already_done.append(permalink)

            # Wait 30 seconds
            print('')
            util.wait(30)


class SubmissionMentionedBot(MentionedBot):
    def start(self):
        """
        Reads submissions from reddit.com/new and check the title and self text for user names.
        """

        super().start()
        already_done = []

        while True:

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
                        if sub_id in already_done:
                            print('Submission was already read.')
                            break

                        # notify the redditor
                        self.notify('submission title', redditor, submission.short_link, title, submission.author.name)

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
                        if sub_id in already_done:
                            print('Submission was already read.')
                            break

                        # notify the redditor
                        self.notify('submission', redditor, submission.short_link, body, submission.author.name)

                if sub_id is not None:
                    already_done.append(sub_id)

            print('')
            util.wait(30)


def main():
    parser = argparse.ArgumentParser(description='Reddit bot for sending notifications to mentioned users.')
    parser.add_argument('-c', '--comments', help='Read comments', required=False, action='store_true')
    parser.add_argument('-s', '--submissions', help='Read submissions', required=False, action='store_true')
    args = parser.parse_args()

    if args.comments:
        CommentMentionedBot().start()
    elif args.submissions:
        SubmissionMentionedBot().start()
    else:
        print('Provide either -c or -s')


if __name__ == '__main__':
    main()
