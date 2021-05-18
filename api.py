from flask import Blueprint, request, abort
from flask_cors import cross_origin
from tables import TweetPost
from flask.json import jsonify
from twitter_bot import tweet
from util import filter_tweet, get_id_from_link
import requests

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
    print(request.json)
    if not request.json or 'text' not in request.json:
        print("a")
        return abort(400)
    text = request.json.get('text')
    reply = request.json.get('reply')
    reply_id = None
    if reply:
        reply_link = request.json.get('reply_link')
        print(reply_link)
        text += "\n \\ Reply Bot \\"
        try:
            reply_id = get_id_from_link(reply_link)
        except (IndexError, ValueError):
            return abort(400)

    if not reply and 'dupan!' not in text.lower():
        return abort(400)
    text = filter_tweet(text)
    link = tweet(text, reply_id=reply_id)
    if link.startswith("http"):
        return jsonify({'success': 'tweet uploaded', 'link': link})
    return abort(400)


@api_app.route("/get-tweet-html")
@cross_origin()
def get_tweet_html():
    link = request.args.get('link')
    if not link:
        return abort(400)
    res = requests.get("https://publish.twitter.com/oembed", params={'url': link})
    print(res.json())
    if res.ok and 'html' in res.json():
        data = res.json()
        if '28fess' in data.get('author_url'):
            html = data.get('html')
            print(html)
            return jsonify({'html': html, 'id': get_id_from_link(data.get('url'))})
        return abort(400)
    return abort(400)

    
