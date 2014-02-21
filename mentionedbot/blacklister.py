import time
import util
from messenger import MentionedBot


class Blacklister:
    KEYWORD_IGNORE = 'ignore'
    KEYWORD_UNIGNORE = 'unignore'
    IGNORED_NOTIFICATION = ("You have been added to my blacklist, message me with 'unignore' to begin receiving "
                            "notifications again.")
    ALREADY_IGNORED_NOTIFICATION = "You are already being ignored."
    NOT_IGNORED_NOTIFICATION = "You are already not being ignored. ;)"
    UNIGNORED_NOTIFICATION = ("You have been removed from my blacklist, message me with 'ignore' to stop receiving "
                              "notifications.")

    blacklist = None
    reddit = None

    def ignore(self, redditor):
        name = redditor.name
        if name in self.blacklist:
            print("'" + name + "' already blacklisted.")
            self.reddit.send_message(name, MentionedBot.NAME, self.ALREADY_IGNORED_NOTIFICATION)
            return
        util.append_to_file(util.BLACKLIST_FILE, name + ',')
        self.blacklist.append(name)
        self.reddit.send_message(name, MentionedBot.NAME, self.IGNORED_NOTIFICATION)
        print("'" + name + "' ignored.")

    def unignore(self, redditor):
        name = redditor.name
        if name not in self.blacklist:
            print("'" + name + "' is not blacklisted.")
            self.reddit.send_message(name, MentionedBot.NAME, self.NOT_IGNORED_NOTIFICATION)
            return
        self.blacklist.remove(name)
        util.write_to_file(util.BLACKLIST_FILE, ','.join(self.blacklist))
        self.reddit.send_message(name, MentionedBot.NAME, self.UNIGNORED_NOTIFICATION)
        print("'" + name + "' unignored.")

    def start(self):
        # Load blacklist
        print('Loading blacklist...'),
        self.blacklist = util.load_list(util.BLACKLIST_FILE, ',')
        print(str(self.blacklist))

        # Log in to reddit
        self.reddit = util.login(MentionedBot.USER_AGENT)

        while True:

            # Retrieve unread messages
            print('\n\nRetrieving unread messages...', end="")
            messages = list(self.reddit.get_unread(limit=None))
            print('[DONE]')

            # Check messages for ignorances
            message_count = messages.__len__()
            print('Unread messages: ' + str(message_count))
            for i in range(0, message_count):
                message = messages[i]

                # Update percent counter
                pcent = i / float(message_count) * 100
                print('\rReading unread messages: [%d%%]' % pcent, end="")
                time.sleep(0.1)

                # Read the message
                body = str(message.body.strip().lower())
                if body == self.KEYWORD_IGNORE: 
                    self.ignore(message.author)
                elif body == self.KEYWORD_UNIGNORE:
                    self.unignore(message.author)

                # Mark as read
                message.mark_as_read()

            # Sleep for 30 seconds
            print('')
            util.wait(30)


if __name__ == '__main__':
    Blacklister().start()