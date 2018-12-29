# Movie Recommender System
### Description
build a movie recommender system using some memory-based recommendation algorithms. The system should be deployed as a Telegram bot and a Web application server.
### Implemetation
Recommender system should at least consists of two parts:
1. bot.py that continues to receive user messages from Telegram. When a message from a user is received, it sends request(s) to the recommendation server, and formats a response to be sent back to the user via Telegram.
2. app.py that implements an HTTP server using Flask. It should provide different routes to accept requests to different functions.
### Dataset Citation
I will use a dataset commonly used in recommender systems research, the MovieLens 100K movie ratings dataset created by GroupLens at the University of Minnesota. Check the Website https://grouplens.org/datasets/movielens/, and read the section “recommended for education and development”. We will use the small dataset with 100,000 ratings.
