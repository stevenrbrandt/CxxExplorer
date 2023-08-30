#!/usr/bin/env python3
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.
# pip3 install python-telegram-bot

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

from subprocess import Popen, PIPE
from traceback import print_exc

import telecling
from time import sleep, time
import datetime

import logging
import re
import os
from signal import SIGINT

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update

from teleplot import plotjson
from colored import colored

pwd_dir = os.path.join(os.environ["HOME"],"cxxcodes")
time_limit = 24*60*60*7 # one week

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

def mtime(fname):
    return time() - os.path.getmtime(fname)

logger = logging.getLogger(__name__)

def get_image(fname):
    with open(fname, "rb") as fd:
        return fd.read()

class Shutdown:
    def __init__(self, pid):
        self.pid = pid
    def end(self):
        os.kill(self.pid, SIGINT)

shutdown = Shutdown(os.getpid())

def shorten(text):
    if len(text) > 4000:
        return text[:4000]+"..."
    return text

def msg(update, text):
    try:
        try:
            image = plotjson(text.strip())
        except:
            image = None
        if image is not None:
            with open(image, "rb") as fd:
                update.message.reply_photo(fd)
            os.remove(image)
        elif re.search(r'</(b|i|strong|em|code|s|strike|del|pre)>', text):
            update.message.reply_html(shorten(text))
        else:
            update.message.reply_text(shorten(text))
    except:
        print(colored("FATAL EXCEPTION","red"))
        print_exc()
        shutdown.end()

def photo(update, fname):
    try:
        with open(fname, "rb") as fd:
            update.message.reply_photo(fd)
    except:
        print_exc()
        shutdown.end()

def start(update: Update, context: CallbackContext) -> None:
    from_user = update.message.from_user
    username = from_user.username
    msg(update, 'Hello, @%s!' % username)


def help_command(update: Update, context: CallbackContext) -> None:
    msg(update, "Send code to the cling server for evaluation")

clients = {}

def cmdproc(update: Update, context: CallbackContext) -> None:
    code = update.message.text
    user = update.effective_user
    from_user = update.message.from_user
    username = from_user.username

    if username not in clients:
        g = re.match(r'(\w{3,100}):(\w{3,100})', code.strip())
        if g:
            fname = os.path.join(pwd_dir, g.group(1)+".txt")
            if os.path.exists(fname):
                mt = mtime(fname)
                with open(fname, "r") as fd:
                    contents = fd.read().strip()
                if mt > time_limit:
                    msg(update, "Password expired")
                elif contents == g.group(2):
                    clients[username] = telecling.ClingServer()
                    msg(update, "Password Approved")
                    photo(update, "thumbsup.png")
                else:
                    sleep(5)
                    print('"%s" != "%s"' % (contents, g.group(2)))
                    msg(update, "Password Failed")
            else:
                msg(update, "Password Failed, file does not exist: %s" % fname)
        else:
            msg(update, "Please enter a valid password")
    else:
        server = clients[username]
        res = server.exec_code(code)
        reply_made = False
        msg(update, "Out[%d]" % server.count)
        for message in res:
            if len(message.strip())==0:
                continue
            msg(update, message)
            reply_made = True
        if not reply_made:
            msg(update, "OK")
            #photo(update, "thumbsup.png")
            #help(context.bot.send_photo) #(chat_id=update.effective_chat.id, photo=thumbs_up)


def main():
    """Start the bot."""
    valid_users = 0
    os.makedirs(pwd_dir, exist_ok=True)
    print("Determining if there any valid user logins...")
    for fname in os.listdir(pwd_dir):
        full = os.path.join(pwd_dir, fname)
        if not full.endswith(".txt"):
            print(colored(f"Skipping '{fname}' because it does not end in .txt","red"))
            continue
        if mtime(full) > time_limit:
            print(colored(f"Skipping '{fname}' because it is expired","red"))
            continue
        if (os.stat(full).st_mode & 0o66) != 0:
            print(colored(f"Skipping '{fname}' because it is readable by others.","red"))
            continue
        c = open(full,"r").read()
        if not re.match(r"^\w{3,100}$", c.strip()):
            print(colored(f"Skipping '{fname}' because the contents are invalid","red"))
            continue
        print(colored("A valid user login was found!","green"))
        valid_users += 1
        break
    if valid_users == 0:
        print(colored(f"No valid users are present in {pwd_dir}.","red"))
        print(f"""
To create a valid user, create a file named ~/cxxcodes/username.txt that contains
a password consisting of letters, numbers, or the underscore. For help in inventing
passwords, please try the following.

    pip3 install --user randpass
    randpass -n 1 -o ~/cxxcodes/username.txt MND
""")
        exit(1)
    print()
    print("Checking for a bot app token...")
    token = os.environ.get("CXXBOT_TOKEN", None)
    if token is None:
        print(colored("No valid token found.","red"))
        print("""
In order to use the bot, you must create a bot and get it's token from the BotFather
(a special Telegram user id). Once you have it,Please set the CXXBOT_TOKEN environment variable
with that token.""")
        exit(3)
    print(colored("Token found! Starting up. Use Ctrl-C to shut down.","green"))
    print()
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, cmdproc))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
