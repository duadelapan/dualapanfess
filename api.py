from flask import Blueprint, request, abort
from flask_cors import cross_origin
from tables import TweetPost
from flask.json import jsonify
from twitter_bot import tweet
from util import filter_tweet

api_app = Blueprint("api_app", __name__, 'static', 'templates')


@api_app.route("/")
@cross_origin()
def test_api():
    tweets = TweetPost.query.order_by(TweetPost.time).all()
    result = {'tweets': []}
    for tweet in tweets:
        tweet_dict = {
            'time': tweet.time,
            'text': tweet.text
        }
        if tweet.sender_line:
            tweet_dict['sender_type'] = 'line'
            tweet_dict['sender'] = tweet.sender_line.name
        else:
            tweet_dict['sender_type'] = 'twitter'
            tweet_dict['sender'] = tweet.sender_twitter.account_id
        result['tweets'].append(tweet_dict)
    return result

@api_app.route("/tweet", methods=["POST"])
@cross_origin()
def post_tweet():
    if not request.json or not 'text' in request.json:
        return abort(400)
    text = request.json.get('text')
    if 'dupan!' not in text.lower():
        return abort(400)
    text = filter_tweet(text)
    link = tweet(text)
    if link.startswith("http"):
        return jsonify({'success': 'tweet uploaded', 'link': link})
    return abort(400)
    
