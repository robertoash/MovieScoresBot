# -*- coding: utf-8 -*-
#!/usr/bin/env python3

# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler  # pip3 install python-telegram-bot --upgrade
import omdb  # pip3 install omdb
import tmdbsimple as tmdb  # pip3 install tmdbsimple
from trakt import Trakt  # pip3 install trakt.py
import requests

from secrets import omdbsecrets as omdbs
from secrets import telegramsecrets as ts
from secrets import traktsecrets as trkts
from secrets import tmdbsecrets as tmdbs
from secrets import utellyapisecrets as uts


# Load secrets
telegramtoken = ts.token
omdb.set_default('apikey', omdbs.omdbkey)
tmdb.API_KEY = tmdbs.key
Trakt.configuration.defaults.client(id=trkts.traktid, secret=trkts.traktkey)
utellyheaders = {'x-rapidapi-host': uts.host, 'x-rapidapi-key': uts.key}


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


CATCHOICE, MOVIESEARCH, MOVIECHOICE, TVSEARCH, TCHOICE = range(5)


class MyClass(object):
    def __init__(self):
        self.movielist = {}

    # Define a few command handlers. These usually take the two arguments update and
    # context. Error handlers also receive the raised TelegramError object in error.
    def start(self, update, context):
        # reply_keyboard = [['Movie', 'TV Show']]
        update.message.reply_text(
            'Hi! I am here to search Scores for you. '
            'You can send /cancel to stop talking to me.\n\n'
            'What movie are you trying to find?')

        return MOVIESEARCH

    def moviesearch(self, update, context):
        # user = update.message.from_user
        logger.info(update.message.text)
        # update.message.reply_text('Searching...')

        """Find Movie Scores"""
        self.movielist = omdb.search_movie(update.message.text)
        if len(self.movielist) == 1:
            rightmovieindex = 0
        elif len(self.movielist) > 1:
            # update.message.reply_text(
            response = []
            response.append("Received " + str(len(self.movielist)) + " results. Please pick the right one:\n")
            count = 0
            for item in self.movielist:
                response.append((str(count + 1) + ". " + item["title"]) + ' (' + str(item["year"]) + ')\n')
                count += 1
            update.message.reply_text("".join(response))
            return MOVIECHOICE
        else:
            update.message.reply_text("No results found.")
            return ConversationHandler.END

        rightmovie = self.movielist[rightmovieindex]
        rightmovieimdbid = rightmovie['imdb_id']

        # Get OMDB ratings (IMDB, RottenTomatoes, Metacritic)
        rightfull = omdb.imdbid(rightmovieimdbid, tomatoes=False)
        ratings = ['"' + rightfull["title"] + '"' + " scored:\n"]
        for item in rightfull["ratings"]:
            if item['source'] == 'Metacritic':
                ratings.append(item['source'] + ': ' + str(item['value']).split("/")[0] + '%\n')
            elif item['source'] == 'Internet Movie Database':
                ratings.append('IMDB: ' + str(round(float(item['value'].split("/")[0])*10)) + '%\n')
            else:
                ratings.append(item['source'] + ': ' + item['value'] + '\n')

        # Get TMDB ratings
        find = tmdb.Find(rightmovieimdbid)
        movie = find.info(external_source='imdb_id')
        tmdbrating = str(round(movie['movie_results'][0]['vote_average']*10))+'%'
        ratings.append('TMDB: ' + tmdbrating + '\n')

        # Get Trakt ratings
        movie = Trakt['search'].lookup(rightmovieimdbid, 'imdb', extended='full')
        moviedict = movie[0].to_dict()
        traktscore = str(round(moviedict['rating']*10))+'%'
        ratings.append('Trakt: ' + traktscore + '\n')

        # Build ratings message
        update.message.reply_text("".join(ratings))

        # Get Trakt trailer
        trakttrailer = moviedict['trailer']
        update.message.reply_text("You can watch the trailer here: " + trakttrailer)

        # Get watch locations from Utelly API (https://rapidapi.com/utelly/api/utelly/endpoints)
        url = "https://utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com/idlookup"
        querystring = {
                        "country": "se",
                        "source_id": rightmovieimdbid,
                        "source": "imdb"
                        }

        response = requests.request("GET", url, headers=utellyheaders, params=querystring)
        respdict = response.json()
        if 'locations' in respdict['collection']:
            locations = ["It is available to watch here:\n"]
            for item in respdict['collection']['locations']:
                locations.append(item['display_name']+'\n')
        else:
            locations = ["This movie is not available for streaming."]

        # Build locations message
        update.message.reply_text("".join(locations))

        return ConversationHandler.END

    def moviechoice(self, update, context):
        msg = update.message.text
        logger.info(msg)
        while True:
            try:
                rightmovieindex = int(msg) - 1
                break
            except ValueError:
                update.message.reply_text("That's not a valid option! Please type the number corresponding to the right title.")
                return MOVIECHOICE

        rightmovie = self.movielist[rightmovieindex]
        rightmovieimdbid = rightmovie['imdb_id']

        # Get OMDB ratings (IMDB, RottenTomatoes, Metacritic)
        rightfull = omdb.imdbid(rightmovieimdbid, tomatoes=False)
        ratings = ['"' + rightfull["title"] + '"' + " scored:\n"]
        for item in rightfull["ratings"]:
            if item['source'] == 'Metacritic':
                ratings.append(item['source'] + ': ' + str(item['value']).split("/")[0] + '%\n')
            elif item['source'] == 'Internet Movie Database':
                ratings.append('IMDB: ' + str(round(float(item['value'].split("/")[0])*10)) + '%\n')
            else:
                ratings.append(item['source'] + ': ' + item['value'] + '\n')

        # Get TMDB ratings
        find = tmdb.Find(rightmovieimdbid)
        movie = find.info(external_source='imdb_id')
        tmdbrating = str(round(movie['movie_results'][0]['vote_average']*10))+'%'
        ratings.append('TMDB: ' + tmdbrating + '\n')

        # Get Trakt ratings
        movie = Trakt['search'].lookup(rightmovieimdbid, 'imdb', extended='full')
        moviedict = movie[0].to_dict()
        traktscore = str(round(moviedict['rating']*10))+'%'
        ratings.append('Trakt: ' + traktscore + '\n')

        # Build ratings message
        update.message.reply_text("".join(ratings))

        # Get Trakt trailer
        trakttrailer = moviedict['trailer']
        update.message.reply_text("You can watch the trailer here: " + trakttrailer)

        # Get watch locations from Utelly API (https://rapidapi.com/utelly/api/utelly/endpoints)
        url = "https://utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com/idlookup"
        querystring = {
                        "country": "se",
                        "source_id": rightmovieimdbid,
                        "source": "imdb"
                        }

        response = requests.request("GET", url, headers=utellyheaders, params=querystring)
        respdict = response.json()
        if 'locations' in respdict['collection']:
            locations = ["It is available to watch here:\n"]
            for item in respdict['collection']['locations']:
                locations.append(item['display_name']+'\n')
        else:
            locations = ["This movie is not available for streaming."]

        # Build locations message
        update.message.reply_text("".join(locations))

        return ConversationHandler.END

    def cancel(self, update, context):
        user = update.message.from_user
        logger.info("User %s has canceled the conversation.", user.first_name)
        update.message.reply_text('Bye! I hope we can talk again some day.')

        return ConversationHandler.END

    def help_command(self, update, context):
        """Send a message when the command /help is issued."""
        update.message.reply_text('Help!')


def main():
    a = MyClass()

    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(telegramtoken, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', a.start)],

        states={
            MOVIESEARCH: [MessageHandler(Filters.text & ~Filters.command, a.moviesearch)],
            MOVIECHOICE: [MessageHandler(Filters.text & ~Filters.command, a.moviechoice)]
        },

        fallbacks=[CommandHandler('cancel', a.cancel)]
    )

    dp.add_handler(conv_handler)

    # on different commands - answer in Telegram
    # dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(CommandHandler("help", help_command))

    # # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, moviesearch))

    # Start the Bot
    updater.start_polling()
    logger.info("MovieScoresBot is Listening...")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
