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
            update.message.reply_html(text)
        else:
            update.message.reply_text(text)
    except:
        print("FATAL EXCEPTION")
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
            fname = "/etc/cxxcodes/"+g.group(1)+".txt"
            if os.path.exists(fname):
                mt = mtime(fname)
                with open(fname, "r") as fd:
                    contents = fd.read().strip()
                if mt > 60*60*24:
                    msg(update, "Password expired")
                elif contents == g.group(2):
                    clients[username] = telecling.ClingServer()
                    msg(update, "Password Approved")
                    photo(update, "thumbsup.png")
                else:
                    sleep(5)
                    msg(update, "Password Failed")
            else:
                msg(update, "Password Faield")
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
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    #updater = Updater("TOKEN", use_context=True)
    updater = Updater("1642213970:AAFll-8DyH-3alACpgR3MbaX6NR4hS71P3Q", use_context=True)

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
