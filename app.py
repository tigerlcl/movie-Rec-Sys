# Application server

import csv
import time
import random
import numpy as np
from scipy import sparse, stats
from collections import defaultdict
from flask import Flask, request, jsonify
app = Flask(__name__)

dataset = defaultdict(list)
movid2link = dict()
movie_info = dict()

def load_data():
    # pre-process the movie, link and ratings-small datasets
    start = time.time()
    ratings_small = './ml-latest-small/ratings.csv'
    movies = './ml-latest-small/movies.csv'
    links = './ml-latest-small/links.csv'

    with open(ratings_small) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dataset[row['userId']].append([row['movieId'],row['rating']])

    with open(links) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            movid2link[row['movieId']] = row['imdbId']

    with open(movies, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            movie_info[row['movieId']] = row['title']

    # generate sparse matrix to '/recommend' route
    row, column, data = [], [], []
    column_index = 0
    for key, value in dataset.items():
        user_column = [int(item[0]) for item in value]  # movie id
        user_row = [column_index] * len(user_column)  # user index from 0
        user_data = [float(item[1]) for item in value]
        column_index += 1
        # concatenate list below to generate Coordinate (row,column) = data
        row += user_row
        column += user_column
        data += user_data
    # end of for loop
    row = np.array(row)
    column = np.array(column)
    data = np.array(data)

    global matrix # for using in '/recommend' route
    matrix = sparse.coo_matrix((data, (row, column))).toarray()
    print('dataset pre-process time: %.3f' % (time.time() - start))

# bind a function to a URL
@app.route('/register',methods= ['POST'])
def register():
    chat_id = str(request.json['chat_id']) # trans int to str
    if chat_id in dataset.keys():
        return jsonify(status='OK', exists = 1)
    else:
        dataset.update({chat_id:[]})
        return jsonify(status='OK', exists = 0)

@app.route('/get_unrated_movie',methods= ['POST'])
def get_unrated_movie():
    chat_id = str(request.json['chat_id'])  # trans int to str
    generate_id = random.choice(list(movid2link))
    if dataset[chat_id] is not None:
        rated_movieId = [item[0] for item in dataset.get(chat_id)]
        while(True):
            if generate_id in rated_movieId:
                generate_id = random.choice(list(movid2link))
            else:
                break
    title, link = movie_info[generate_id], movid2link[generate_id]
    # composite movie url, max digit is 7
    # The method zfill() pads string on the left with zeros to fill width.
    url = 'https://www.imdb.com/title/tt' + link.zfill(7)
    return jsonify( id = generate_id, title = title, url = url)

@app.route('/rate_movie', methods=['POST'])
def submit_rate():
    chat_id, movie_id = str(request.json['chat_id']), request.json['movie_id']
    rating = request.json['rate'][-1] # index slice to keep the last digit
    if movie_id not in [item[0] for item in dataset[chat_id]]:
        dataset[chat_id].append([movie_id,rating])
        return jsonify(status = 'success')
    else:
        return jsonify(status = 'duplicated')

@app.route('/recommend',methods= ['POST'])
def recommend():
    start = time.time()
    chat_id = str(request.json['chat_id'])  # trans int to str
    top = request.json['top'] # use it in the later part
    movie_list = []
    if len(dataset[chat_id]) < 5:
        return jsonify( movies = movie_list )
    else:
        # generate real user sparse row of ratings
        user_column = np.array([int(item[0]) for item in dataset[chat_id]])  # movie id
        user_data = np.array([float(item[1]) for item in dataset[chat_id]])
        user_record = np.zeros(matrix.shape[1]) # np.zeros()
        np.put(user_record,user_column,user_data) # np.put()
        # find the most similar user with real user
        max_sim = 0
        selected_user = None
        for item in matrix:
            user_sim, _ = stats.pearsonr(user_record, item) # Pearson Correlation
            if user_sim > max_sim:
                max_sim = user_sim
                selected_user = item # get user movie rating data

        r_mean_0 = np.mean([r for r in selected_user if r > 0])
        r_mean_1 = np.mean([r for r in user_record if r >0])

        pred_list = []
        for i in range(len(user_record)):
            if selected_user[i] != 0 and user_record[i] == 0: # find out movies rated by select_user but not rated by you
                pred = r_mean_1+ (max_sim * (selected_user[i]-r_mean_0))
                pred_list.append((pred, i))
        # sort list of tuple:(pred,i) by pred
        pred_list.sort(key=lambda x:x[0], reverse=True)
        # get top 3 movie list
        for item in pred_list[:top]:
            movie_id = str(item[1]) # int -> str
            title, link = movie_info[movie_id], movid2link[movie_id]
            url = 'https://www.imdb.com/title/tt' + link.zfill(7)
            movie_list.append({'title':title,'url':url})

        print('recommend time cost: %.3f s' % (time.time() - start))
        return jsonify(movies = movie_list )

if __name__ == '__main__':
    app.data = load_data()
    app.run()#debug=True)
