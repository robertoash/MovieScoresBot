FROM python:3
ADD moviescores.py /
ADD /secrets /secrets
RUN pip install python-telegram-bot --upgrade
RUN pip install omdb
RUN pip install tmdbsimple
RUN pip install trakt.py
CMD [ "python", "./moviescores.py" ]
