from flask import Blueprint, request
from flask_cors import cross_origin
from tables import TweetPost, ReplyToken, db
from flask.json import jsonify
from twitter_bot import tweet
from util import filter_tweet, get_id_from_link
from http import HTTPStatus
import uuid
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
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'Invalid request'}), HTTPStatus.BAD_REQUEST
    text = request.json.get('text')
    reply = request.json.get('reply')
    reply_token = request.json.get('reply_token')
    reply_id = None
    reply_token_data = None
    if reply:
        reply_token_data = ReplyToken.query.get(reply_token)
        print(reply_token_data)
        if not reply_token_data:
            return jsonify({'error': 'Token error, please reload the page'}), HTTPStatus.BAD_REQUEST
        reply_link = request.json.get('reply_link')
        print(reply_link)
        text += "\n \\ Reply Bot \\"
        try:
            reply_id = get_id_from_link(reply_link)
        except (IndexError, ValueError):
            return jsonify({'error': 'Invalid link'}), HTTPStatus.BAD_REQUEST

    if not reply and 'dupan!' not in text.lower():
        return jsonify({'error': 'dupan! must included'}), HTTPStatus.BAD_REQUEST
    text = filter_tweet(text)
    link = tweet(text, reply_id=reply_id)
    if reply:
        db.session.remove(reply_token_data)
        db.session.commit()
    if link.startswith("http"):
        return jsonify({'success': 'tweet uploaded', 'link': link}), HTTPStatus.OK
    return jsonify({'error': 'Upload failed. Try again later.'}), HTTPStatus.FAILED


@api_app.route("/get-tweet-html")
@cross_origin()
def get_tweet_html():
    link = request.args.get('link')
    if not link:
        return jsonify({'error': 'Invalid request, no link detected'}), HTTPStatus.BAD_REQUEST
    res = requests.get("https://publish.twitter.com/oembed", params={'url': link})
    if res.ok and 'html' in res.json():
        data = res.json()
        if '28fess' in data.get('author_url'):
            html = data.get('html')
            reply_token = ReplyToken(token=str(uuid.uuid4()))
            db.session.add(reply_token)
            db.session.commit()
            print(html)
            return jsonify({
                'html': html,
                'id': get_id_from_link(data.get('url')),
                'reply_token': reply_token.token
            }), HTTPStatus.OK
        return jsonify({'error': 'Harus tweet yang berasal dari akun 28FESS'}), HTTPStatus.BAD_REQUEST
    return jsonify({'error': 'Link invalid.'}), HTTPStatus.BAD_REQUEST


