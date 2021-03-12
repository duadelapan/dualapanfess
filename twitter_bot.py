import io
import os
import time

import requests
import tweepy
from TwitterAPI import TwitterAPI
from requests_oauthlib import OAuth1

import util
from tables import db, TwitterAccount

ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
API_KEY = os.environ.get("TWITTER_API_KEY")
API_KEY_SECRET = os.environ.get("TWITTER_API_SECRET")
auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
CANCEL_OPTIONS = [
    {
        "label": "/canceltweet",
        "description": "Cancel Tweet",
        "metadata": "external_id_1"
    }
]

CONFIRM_OPTIONS = [
    {
        "label": "/send",
        "description": "Send Tweet",
        "metadata": "external_id_1"
    },
    {
        "label": "/canceltweet",
        "description": "Cancel Tweet",
        "metadata": "external_id_2"
    }
]


class MessageData:
    def __init__(self, text, media_url=None, media_id=None):
        self.text = text
        self.media_url = media_url
        self.media_id = media_id
        if media_id:
            print(media_id)

    def get_dict(self):
        res_dict = {'text': self.text}
        if self.media_url:
            res_dict['entities'] = self.media_url
        return res_dict


class DirectMessage:
    def __init__(self, recipient_id=None, sender_id=None, source_app_id=None, message_data: MessageData = None):
        self.recipient_id = recipient_id
        self.sender_id = sender_id
        self.source_app_id = source_app_id
        self.message_data = message_data

    def get_dict(self):
        return {"event":
                    {"type": "message_create",
                     "message_create":
                         {"target":
                              {"recipient_id": self.recipient_id},
                          "message_data": self.message_data.get_dict()
                          }}}


def upload_media(url):
    auth_tweet = OAuth1(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    response = requests.get(url, auth=auth_tweet)
    file = io.BytesIO(response.content)
    media = api.media_upload(filename="twitter_img", file=file)
    file.close()
    return media.media_id


def test_tweet():
    return api.verify_credentials()


def init_api_object():
    # user authentication
    api = TwitterAPI(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return api


def get_quick_reply_dict(label, description=None):
    quick_reply_dict = {'label': label}
    if description:
        quick_reply_dict['description'] = description
    return quick_reply_dict


def make_quick_reply_options(options):
    for i in range(len(options)):
        options[i]['metadata'] = f"external_id_{i}"
    return options


def send_confirm_message(user_id, message):
    dm_quick_reply_options(user_id,
                           f"❗❗CONFIRMATION❗❗\n\n{message}\n\n"
                           "/send to tweet 📨\n"
                           "/canceltweet to cancel ❌",
                           CONFIRM_OPTIONS)


def tweet(msg: str, file=None, url=None):
    msg = util.clear_tweet(msg)
    if len(msg) > 550:
        return f"❗TWEET ERROR❗\n{len(msg)} exceeds the characters limit (550)."
    media = None
    msg2 = None
    if len(msg) > 280:
        space_index = util.last_index(msg[:273], " ")
        msg_is_split = False
        if space_index and space_index > 200:
            space_index += 1
            msg2 = msg[space_index:]
            if len(msg2) <= 280:
                msg = msg[:space_index] + "(cont)"
                msg_is_split = True
        if not msg_is_split:
            msg2 = msg[273:]
            msg = msg[:273] + " (cont)"
    try:
        if file:
            media = api.media_upload(filename="line_img", file=file)
        if media:
            post = api.update_status(msg, media_ids=[media.media_id])
        elif url:
            post = api.update_status(msg, media_ids=[upload_media(url)])
        else:
            post = api.update_status(msg)
        if msg2:
            try:
                api.update_status(status=msg2, in_reply_to_status_id=post.id)
            except tweepy.error.TweepError as e:
                print(e)
                api.destroy_status(post)
                return "Tweet failed. Please try again."
        return f"https://twitter.com/{post.user.screen_name}/status/{post.id}"
    except tweepy.error.TweepError as e:
        print(e)
        return "Tweet failed. Please try again."


def dm_quick_reply_options(recipient_id, text, options):
    auth_tweet = OAuth1(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    url = "https://api.twitter.com/1.1/direct_messages/events/new.json"
    header = {
        'content-type': 'application/json'
    }
    params = {
        'event': {'type': 'message_create',
                  'message_create': {
                      'target': {'recipient_id': recipient_id},
                      'message_data': {'text': text,
                                       'quick_reply': {
                                           'type': 'options',
                                           'options': options
                                       }}
                  }
                  }
    }
    response = requests.post(url, auth=auth_tweet, json=params, headers=header)
    return response


def process_direct_message_event(message_obj: DirectMessage):
    message_text = message_obj.message_data.text
    message_text_lower = message_text.lower()
    userID = message_obj.sender_id
    account = TwitterAccount.query.get(userID)

    if not account:
        account = TwitterAccount(account_id=userID)
        db.session.add(account)
        db.session.commit()

    if "dupan!" in message_text.lower():
        account.tweet_phase = "confirm"
        account.next_tweet_msg = message_text
        account.last_tweet_req = util.datetime_now_string()
        if message_obj.message_data.media_url:
            account.next_tweet_msg = message_text[:util.last_index(message_text, " ")]
            account.img_soon = True
            account.tweet_phase = "confirm " + message_obj.message_data.media_url
        send_confirm_message(userID, account.next_tweet_msg)
        db.session.commit()

    elif message_text_lower == "/tweet28fess":
        account.tweet_phase = "from"
        account.next_tweet_msg = "from: "
        account.last_tweet_req = util.datetime_now_string()
        db.session.commit()
        dm_quick_reply_options(userID,
                               f"from: \n\n/canceltweet to cancel ❌\n"
                               f"request: {time.time()}",
                               CANCEL_OPTIONS)

    else:
        phase = account.tweet_phase
        if phase:
            if message_text_lower == "/canceltweet":
                util.clear_account_tweet_data(account)
                api.send_direct_message(userID,
                                        "Tweet Cancelled\n"
                                        f"request: {time.time()}")
            else:
                if util.check_timeout(account.last_tweet_req, 300):
                    now = util.datetime_now_string()
                    account.last_tweet_req = now
                    if account.img_soon and phase == "img" and message_obj.message_data.media_url:
                        account.tweet_phase = "confirm " + message_obj.message_data.media_url
                        send_confirm_message(userID, account.next_tweet_msg)
                        account.last_tweet_req = util.datetime_now_string()
                    elif phase == "from":
                        account.tweet_phase = "to"
                        account.next_tweet_msg += message_text + "\nto: "
                        dm_quick_reply_options(userID,
                                               f"{account.next_tweet_msg} \n\n/canceltweet to cancel ❌\n"
                                               f"request: {time.time()}", CANCEL_OPTIONS)
                    elif phase == "to":
                        account.tweet_phase = "text"
                        account.next_tweet_msg += message_text + "\n"
                        dm_quick_reply_options(userID,
                                               f"{account.next_tweet_msg}"
                                               f"message: (can attach an image)\n\n/canceltweet to cancel ❌\n"
                                               f"request: {time.time()}", CANCEL_OPTIONS)
                    elif phase == "text":
                        msg = account.next_tweet_msg + message_text
                        account.tweet_phase = "confirm"
                        account.next_tweet_msg = msg
                        if message_obj.message_data.media_url:
                            account.next_tweet_msg = msg[:util.last_index(msg, " ")]
                            account.img_soon = True
                            account.tweet_phase = "confirm " + message_obj.message_data.media_url
                        send_confirm_message(userID, account.next_tweet_msg)
                    elif phase.startswith("confirm") and message_text_lower == "/send":
                        if account.img_soon:
                            msg_media_url = phase.split(" ")[-1]
                            url = tweet(account.next_tweet_msg, url=msg_media_url)
                        else:
                            url = tweet(account.next_tweet_msg)
                        if url.startswith("https"):
                            account.last_tweet = now
                            message = f"Tweet Posted.{url}"
                        else:
                            message = url
                        api.send_direct_message(userID,
                                                message)
                        util.clear_account_tweet_data(account)
                else:
                    util.clear_account_tweet_data(account)
            db.session.commit()
    return None


def process_like_event(event_obj):
    user_handle = event_obj.get('user', {}).get('screen_name')

    print('This user liked one of your tweets: %s' % user_handle)

    return None


def process_follow_event(follower):
    name = follower.get('name')
    follower_id = follower.get('id')
    try:
        api.send_direct_message(follower_id,
                                f"✨ WELCOME TO 28FESS {name.upper()}! ✨\n\n"
                                f"Untuk tweet melalui akun ini, dapat dengan:\n"
                                f"- chat menggunakan 𝗱𝘂𝗽𝗮𝗻!\n"
                                f"- keyword /𝘁𝘄𝗲𝗲𝘁𝟮𝟴𝗙𝗘𝗦𝗦 untuk kirim menfess dengan format 'from, to'\n\n"
                                f"kirim chat melalui 𝗗𝗠 atau 𝗢𝗔 𝗟𝗜𝗡𝗘 𝟮𝟴𝗙𝗘𝗦𝗦 𝗕𝗢𝗧\n"
                                f"🛡(PRIVASI TERJAGA)🛡\n\n"
                                f"Segera kirim menfess pertamamu!\n"
                                f"https://28fess.carrd.co/")
    except tweepy.TweepError as e:
        print(e)
        api.send_direct_message(follower_id,
                                f"✨ SELAMAT DATANG DI 28FESS {name.upper()}! ✨\n\n"
                                f"Untuk tweet melalui akun ini, dapat dengan:\n"
                                f"- chat menggunakan 𝗱𝘂𝗽𝗮𝗻!\n"
                                f"- keyword /𝘁𝘄𝗲𝗲𝘁𝟮𝟴𝗙𝗘𝗦𝗦 untuk kirim menfess dengan format 'from, to'\n\n"
                                f"kirim chat melalui 𝗗𝗠 atau 𝗢𝗔 𝗟𝗜𝗡𝗘 𝟮𝟴𝗙𝗘𝗦𝗦 𝗕𝗢𝗧\n"
                                f"🛡(PRIVASI TERJAGA)🛡\n\n"
                                f"Segera kirim menfess pertamamu!\n\n"
                                f"{time.time()}")
