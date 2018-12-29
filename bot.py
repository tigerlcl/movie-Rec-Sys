# Client-bot side

import time
import requests
import logging
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)

def handle(msg):
    # Get text or data from the message
    text = msg.get("text", None)
    data = msg.get("data", None)
    chat_id = None

    if data is not None:
        # This is a message from a custom keyboard
        chat_id = msg["message"]["chat"]["id"]
        content_type = "data"
    elif text is not None:
        # This is a text message from the user
        chat_id = msg["chat"]["id"]
        content_type = "text"
    else:
        # This is a message we don't know how to handle
        content_type = "unknown"

    if content_type == "text":
        message = msg["text"]
        logging.info("Received from chat_id={}: {}".format(chat_id, message))

        if message == "/start":
            # Check against the server to see if the user is new or not
            conn = requests.post("http://127.0.0.1:5000/register", json={'chat_id': chat_id})
            flag = conn.json()['exists']
            if flag == 0:
                print('register done!')
                bot.sendMessage(chat_id, "Welcome!")
            else:
                print('registered already!')
                bot.sendMessage(chat_id, "Welcome back!")

        elif message == "/rate":
            # Ask the server to return a random movie, and ask the user to rate the movie
            conn = requests.post("http://127.0.0.1:5000/get_unrated_movie",json={'chat_id': chat_id})
            global movie_id # use it to submit in '/rate_movie' route
            movie_id= conn.json()['id']
            resp = conn.json()['title'] + ':'+ conn.json()['url']
            bot.sendMessage(chat_id, resp)

            # Create a custom keyboard to let user enter rating
            my_inline_keyboard = [[
                InlineKeyboardButton(text='1', callback_data='rate_movie_1'),
                InlineKeyboardButton(text='2', callback_data='rate_movie_2'),
                InlineKeyboardButton(text='3', callback_data='rate_movie_3'),
                InlineKeyboardButton(text='4', callback_data='rate_movie_4'),
                InlineKeyboardButton(text='5', callback_data='rate_movie_5')
            ]]
            keyboard = InlineKeyboardMarkup(inline_keyboard=my_inline_keyboard)
            bot.sendMessage(chat_id, "How do you rate this movie?", reply_markup=keyboard)

        elif message == "/recommend":
            # Ask the server to generate a list of
            # recommended movies to the user
            # TODO
            conn = requests.post("http://127.0.0.1:5000/recommend",json={'chat_id': chat_id,'top':3})
            resp = conn.json()['movies']
            if len(resp) ==0:
                msg = 'You have not rated enough movies, we cannot generate recommendation for you'
                bot.sendMessage(chat_id, msg)
            else:
                # resp contains list of dict
                bot.sendMessage(chat_id, 'system recommend TOP3 movies here')
                for item in resp:
                    msg = item['title'] + ' : ' + item['url']
                    bot.sendMessage(chat_id,msg)

        else:
            # Some command that we don't understand
            bot.sendMessage(chat_id, "I don't understand your command.")

    elif content_type == "data":
        # This is data returned by the custom keyboard
        # Extract the movie ID and the rating from the data
        # and then send this to the server
        conn = requests.post("http://127.0.0.1:5000/rate_movie",
                             json={'chat_id': chat_id, 'rate':data, 'movie_id':movie_id})
        if conn.json()['status'] == 'success':
            logging.info("Received rating: {}".format(data))
            bot.sendMessage(chat_id, "Your rating is received!")
        # bonus part
        if conn.json()['status'] == 'duplicated':
            logging.info("received duplicated rate on the same movie")
            bot.sendMessage(chat_id, "don't over-click rate area ")

if __name__ == "__main__":
    # Povide your bot's token
    bot = telepot.Bot("587437196:AAGKtoViNhSK7gBePn2DtRJlvBbzXl-kBkM")
    print('initializing bot...')
    MessageLoop(bot, handle).run_as_thread()

    while True:
        time.sleep(10)
