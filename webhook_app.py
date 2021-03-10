from flask import Blueprint, request
from http import HTTPStatus
import twitter_bot, hashlib, hmac, base64, os, json
from twitter_bot import MessageData, DirectMessage

webhook_app = Blueprint("webhook_app", __name__, 'static', 'templates')
API_KEY_SECRET = os.environ.get("TWITTER_API_SECRET")
CURRENT_USER_ID = "1366012060602044418"


# The GET method for webhook should be used for the CRC check
@webhook_app.route("/", methods=["GET"])
def twitter_crc_validation():
    crc = request.args['crc_token']

    validation = hmac.new(
        key=bytes(API_KEY_SECRET, 'utf-8'),
        msg=bytes(crc, 'utf-8'),
        digestmod=hashlib.sha256
    )
    digested = base64.b64encode(validation.digest())
    response = {
        'response_token': 'sha256=' + format(str(digested)[2:-1])
    }
    print('responding to CRC call')

    return json.dumps(response)


# The POST method for webhook should be used for all other API events
@webhook_app.route("/", methods=["POST"])
def twitter_event_received():
    request_json = request.get_json()

    # dump to console for debugging purposes
    # print(json.dumps(request_json, indent=4, sort_keys=True))

    if 'favorite_events' in request_json.keys():
        # Tweet Favourite Event, process that
        like_object = request_json['favorite_events'][0]
        user_id = like_object.get('user', {}).get('id')

        # event is from myself so ignore (Favourite event fires when you send a DM too)
        if user_id == CURRENT_USER_ID:
            return '', HTTPStatus.OK

        twitter_bot.process_like_event(like_object)

    elif 'direct_message_events' in request_json.keys():
        # DM recieved, process that
        event_type = request_json['direct_message_events'][0].get("type")
        message_object = request_json['direct_message_events'][0].get('message_create', {})
        message_sender_id = message_object.get('sender_id')

        # event type isnt new message so ignore
        if event_type != 'message_create':
            return '', HTTPStatus.OK

        # message is from myself so ignore (Message create fires when you send a DM too)
        if message_sender_id == CURRENT_USER_ID:
            return '', HTTPStatus.OK
        message_data = message_object.get('message_data')
        media = message_data.get('attachment', {})
        media_url = None
        media_id = None
        if media:
            media_url = media.get('media').get('media_url')
            media_id = media.get('media').get('id')
        data = MessageData(message_data.get('text', ''), media_url=media_url, media_id=media_id )
        message = DirectMessage(
            message_object.get('recipient_id'),
            message_object.get('sender_id'),
            message_object.get('source_app_id'),
            data
        )
        twitter_bot.process_direct_message_event(message)
    elif 'follow_events' in request_json.keys():
        dm_event = request_json['follow_events'][0]
        follower = dm_event.get('source')
        twitter_bot.process_follow_event(follower)

    else:
        # Event type not supported
        return '', HTTPStatus.OK

    return '', HTTPStatus.OK

