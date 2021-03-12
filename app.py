from flask import Flask
import io
import random
from datetime import datetime, timedelta
from html import unescape
import requests
from flask import request, abort
from googleapiclient import discovery
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, \
    ButtonsTemplate, URIAction, ImageMessage, QuickReply, QuickReplyButton, MessageAction, JoinEvent
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from google_search import search_google
from tables import db, LineAccount, LineGroup
from twitter_bot import tweet, test_tweet, check_timeout
from webhook_app import webhook_app
from question import add_question, add_answer, delete_all, delete_question, get_question_str, search_question
import os
import json
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "8BYkEfBA6O6donzWlSihBXox7C0sKR6b")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.register_blueprint(webhook_app, url_prefix="/webhook")
db.app = app
db.init_app(app)
db.create_all()
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
MY_LINE_ID = "Ub2cd3e3460664f1ea60deab2b3863c55"


def get_delta_time(year, month, day=0, hour=0):
    now = datetime.utcnow()
    now = now + timedelta(hours=7)
    snm = datetime(year=year, month=month, day=day, hour=hour)
    delta = snm - now
    day = delta.days
    clock = str(delta).split(", ")[-1]
    hour, minute, second = clock.split(':')
    second = second.split('.')[0]
    return day, hour, minute, second


def get_youtube_url(query):
    with open("./rest.json") as f:
        service = json.load(f)

    yt = discovery.build_from_document(service,
                                       developerKey=YOUTUBE_API_KEY)

    req = yt.search().list(q=query, part='snippet', maxResults=1, type='video')
    res = req.execute()
    return ('https://youtu.be/' + res['items'][0]['id']['videoId']), unescape(res['items'][0]['snippet']['title'])


def get_emoji_str(hex_code):
    return f"{chr(int(f'{hex_code}', 16))}"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(JoinEvent)
def handle_join_event(event):
    if event.source.type == "group":
        name = line_bot_api.get_group_summary(event.source.group_id).group_name
    else:
        name = ""
    message = f"Halo {name}!\n\n" \
              "Untuk daftar command, ketik /command\n\n" \
              "28 Menfess Twitter Bot:\n" \
              "Keywords: \n" \
              "/tweet28fess\n" \
              "/tweet28fessimg\n\n" \
              "Untuk fess tweet, bisa menggunakan command di atas atau chat langsung dengan kata kunci \n" \
              "dupan!\n\n" \
              "FOLLOW\n" \
              "https://twitter.com/28FESS?s=20"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(message)
    )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    account = LineAccount.query.filter_by(account_id=event.source.user_id).first()
    if account:
        if account.img_soon and account.tweet_phase == "img":
            if check_timeout(account.last_tweet_req, 300):
                account.tweet_phase = "confirm " + event.message.id
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(f"❗❗CONFIRMATION❗❗\n\n{account.next_tweet_msg}\n\n"
                                    f"/send to tweet {get_emoji_str('0x1000A5')}\n"
                                    f"/canceltweet to cancel ❌",
                                    quick_reply=QuickReply(items=[
                                        QuickReplyButton(action=MessageAction("SEND", "/send")),
                                        QuickReplyButton(
                                            action=MessageAction("CANCEL", "/canceltweet"))
                                    ]))
                )
            account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
            db.session.commit()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.lower()
    account = LineAccount.query.filter_by(account_id=event.source.user_id).first()
    if event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if not group:
            group = LineGroup(id=event.source.group_id)
            group.name = line_bot_api.get_group_summary(group.id).group_name
            db.session.add(group)
            db.session.commit()
    if not account:
        account = LineAccount(account_id=event.source.user_id)
        try:
            account.name = line_bot_api.get_profile(account.account_id).display_name
        except LineBotApiError:
            pass
        db.session.add(account)
        db.session.commit()
    elif not account.name:
        try:
            account.name = line_bot_api.get_profile(account.account_id).display_name
        except LineBotApiError:
            pass
        else:
            db.session.commit()
    if account.is_add_question:
        account.is_add_question = False
        db.session.commit()
        add_answer(account.question_id, event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(get_question_str(account.question_id))
        )
    elif "dupan!" in user_message:
        account.tweet_phase = "img ask"
        account.next_tweet_msg = event.message.text
        account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Want to attach an image?\n\n"
                            f"/yes {get_emoji_str('0x1000A5')} or /no {get_emoji_str('0x1000A6')}\n"
                            "/canceltweet to cancel ❌",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction("YES", "/yes")),
                                QuickReplyButton(action=MessageAction("NO", "/no")),
                                QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                            ]))
        )
    elif user_message == "snmptn":
        day, hour, minute, second = get_delta_time(2021, 3, 22, 15)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text=f"Pengumuman SNMPTN\n"
                         f"🕒{day} hari {hour} jam {minute} menit {second} detik lagi 😲",
                template=ButtonsTemplate(
                    thumbnail_image_url='https://statik.tempo.co/data/2019/12/01/id_893849/893849_720.jpg',
                    title='Pengumuman SNMPTN',
                    text=f"{day} hari {hour} jam {minute} menit {second} detik lagi.",
                    actions=[
                        URIAction(
                            label='Live Countdown',
                            uri='https://snmptn.arsaizdihar.com/'
                        )
                    ]
                )
            ))
    elif user_message == "sbmptn":
        day, hour, minute, second = get_delta_time(2021, 4, 12)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"SBMPTN\n"
                                 f"{get_emoji_str('0x100071')}{day} hari {hour} jam {minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
    elif user_message == "ppkb":
        day, hour, minute, second = get_delta_time(2021, 3, 26, 13)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"PENGUMUMAN PPKB\n"
                                 f"{get_emoji_str('0x100071')}{day} hari {hour} jam {minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
    elif user_message == "/testtweet":
        test = test_tweet()
        if test:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("success")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("fail")
                )
    elif user_message.startswith('/youtube ') and len(user_message) > 9:
        query = user_message[9:]
        title, url = get_youtube_url(query)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{title}\n{url}")
        )

    elif user_message == "/meme":
        response = requests.get('https://meme-api.herokuapp.com/gimme')
        url = response.json()['url']
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url=url, preview_image_url=url)
        )
    elif user_message.startswith("/number"):
        if user_message == "/number":
            message = "Keywords: \n" \
                      "- /number (number)\n" \
                      "- /number/random"
        else:
            res_type = random.choice(('math', 'trivia'))
            req = user_message[7:]
            if req == "/random":
                response = requests.get('http://numbersapi.com/random/' + res_type)
                message = response.text
            else:
                try:
                    req = int(req)
                except ValueError:
                    message = "Invalid request"
                else:
                    response = requests.get('http://numbersapi.com/' + str(req) + "/" + res_type)
                    message = response.text
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )

    elif user_message == "/cat":
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        data = response.json()
        url = data[0]['url']
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(url, url)
        )
    elif user_message == "/tweet28fess":
        account.tweet_phase = "from"
        account.next_tweet_msg = "from: "
        account.last_tweet_req = datetime.utcnow().strftime(TIME_FORMAT)
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(f"from: \n\n/canceltweet to cancel ❌",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                            ]))
        )
    elif user_message == "/tumbal" and event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if not group:
            group = LineGroup(id=event.source.group_id)
            db.session.add(group)
        group.name = line_bot_api.get_group_summary(group.id).group_name
        if group.phase == "tumbal":
            user_name = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id).display_name
            if user_name not in group.data.split("\n"):
                group.data += "\n" + user_name
                group.member_ids += "\n" + event.source.user_id
        else:
            group.phase = "tumbal"
            group.data = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id).display_name
            group.member_ids = event.source.user_id
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Daftar Tumbal" + "\n" + group.data)
        )
        db.session.commit()
    elif user_message == "/tumbalkelar" and event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if group:
            if group.phase == "tumbal" and group.data:
                member_ids = group.member_ids.split("\n")
                member = line_bot_api.get_group_member_profile(event.source.group_id, random.choice(member_ids))
                if member.picture_url:
                    messages = [
                        TextSendMessage("Yang jadi tumbal: " + member.display_name),
                        ImageSendMessage(member.picture_url, member.picture_url)
                    ]
                else:
                    messages = TextSendMessage("Yang jadi tumbal: " + member.display_name),
                line_bot_api.reply_message(
                    event.reply_token,
                    messages=messages
                )
                group.data = ""
                group.phase = ""
                group.member_ids = ""
                db.session.commit()
    elif user_message.startswith("/google ") and len(user_message) > len("/google "):
        query = event.message.text[8:]
        results = search_google(query)
        message = ""
        for result in results:
            message += f"{result['title']}\n{result['description']}\n{result['link']}\n\n"
        message = message[:-2]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )
    elif user_message.startswith("/pilih ") and ", " in user_message:
        pilihan = event.message.text[7:].split(", ")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(random.choice(pilihan))
        )
    elif user_message.startswith("/kerangajaib "):
        random.seed(user_message)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(random.choice(["iya", "tidak"]))
        )
        random.seed()
    elif user_message.startswith("/balik ") and len(user_message) > len("/balik "):
        message = " ".join("".join(reversed(x)) for x in event.message.text[7:].split(" "))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )
    elif user_message == "/balik":
        if account.tweet_phase == "balik":
            account.tweet_phase = ""
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Balik mode off")
            )
        else:
            account.tweet_phase = "balik"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Balik mode on")
            )
        db.session.commit()
    elif user_message.startswith("/addq ") and len(user_message) > len("/addq "):
        if account.question_access:
            account.is_add_question = True
            question = event.message.text[6:]
            question_id = add_question(question)
            if question_id:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(f"Question Added. ID: {question_id}\nAnswer: ")
                )
                account.question_id = question_id
                db.session.commit()
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(f"Question already exist.\n{search_question(question)}")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Access Denied.")
            )

    elif user_message.startswith("/addans ") and len(user_message) > len("/addans "):
        if account.question_access:
            message_list = event.message.text.split(" ")
            question_id = message_list[1]
            try:
                int(question_id)
                answer = " ".join(message_list[2:])
            except ValueError:
                message = "error: invalid input"
            except IndexError:
                message = "error: invalid input"
            else:
                if add_answer(question_id, answer):
                    message = get_question_str(question_id)
                else:
                    message = "ID invalid"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(message)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Access Denied.")
            )

    elif user_message.startswith("/searchq ") and len(user_message) > len("/searchq "):
        if account.question_access:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(search_question(event.message.text[9:]))
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Access Denied.")
            )

    else:
        if account:
            phase = account.tweet_phase
            if phase and phase == "balik":
                message = " ".join("".join(reversed(x)) for x in event.message.text.split(" "))
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(message)
                )
            elif phase:
                if user_message == "/canceltweet":
                    account.tweet_phase = ""
                    account.next_tweet_msg = ""
                    account.last_tweet_req = ""
                    account.img_soon = False
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage("Tweet Cancelled")
                    )
                else:
                    if check_timeout(account.last_tweet_req, 300):
                        now = datetime.utcnow().strftime(TIME_FORMAT)
                        account.last_tweet_req = now
                        if phase == "from":
                            account.tweet_phase = "to"
                            account.next_tweet_msg += event.message.text + "\nto: "
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(f"to: \n\n/canceltweet to cancel ❌",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "to":
                            account.tweet_phase = "text"
                            account.next_tweet_msg += event.message.text + "\n"
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(f"message: \n\n/canceltweet to cancel ❌",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "text":
                            msg = account.next_tweet_msg + event.message.text
                            account.tweet_phase = "img ask"
                            account.next_tweet_msg = msg
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage("Want to attach an image?\n\n"
                                                f"/yes {get_emoji_str('0x1000A5')} or /no {get_emoji_str('0x1000A6')}\n"
                                                "/canceltweet to cancel ❌",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("YES", "/yes")),
                                                    QuickReplyButton(action=MessageAction("NO", "/no")),
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "img ask":
                            if user_message == "/yes":
                                account.img_soon = True
                                account.tweet_phase = "img"
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage("Send an image within 5 min.\n\n"
                                                    f"/canceltweet to cancel ❌",
                                                    quick_reply=QuickReply(items=[
                                                        QuickReplyButton(
                                                            action=MessageAction("CANCEL", "/canceltweet"))
                                                    ]))
                                )
                            elif user_message == "/no":
                                account.tweet_phase = "confirm"
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage("❗❗CONFIRMATION❗❗\n\n"
                                                    f"{account.next_tweet_msg}\n\n"
                                                    f"/send to tweet ✉️\n"
                                                    f"/canceltweet to cancel ❌",
                                                    quick_reply=QuickReply(items=[
                                                        QuickReplyButton(action=MessageAction("SEND", "/send")),
                                                        QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                    ]))
                                )
                        if phase.startswith("confirm") and user_message == "/send":
                            account.tweet_phase = ""
                            account.last_tweet_req = ""
                            if account.img_soon:
                                msg_media_id = phase.split(" ")[-1]
                                pic = line_bot_api.get_message_content(msg_media_id)
                                file = io.BytesIO(pic.content)
                                url = tweet(account.next_tweet_msg, file)
                                file.close()
                                account.img_soon = False
                            else:
                                url = tweet(account.next_tweet_msg)
                            account.next_tweet_msg = ""
                            if url.startswith("https"):
                                account.last_tweet = now
                                message = f"Tweet Posted.\nurl: {url}"
                            else:
                                message = url
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(message)
                            )
                db.session.commit()
    if account.account_id == MY_LINE_ID:
        if user_message.startswith("/getid "):
            search_name = event.message.text[7:]
            accounts = LineAccount.query.filter(LineAccount.name.ilike(f"%{search_name}%"))
            if accounts:
                msg_ids = '\n'.join([search_account.account_id for search_account in accounts])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(f"ID:\n{msg_ids}")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage("No account found.")
                )
        elif user_message.startswith("/addacc "):
            requested_account = LineAccount.query.get(event.message.text[8:])
            requested_account.question_access = True
            db.session.commit()

        elif user_message.startswith("/removeacc "):
            requested_account = LineAccount.query.get(event.message.text[11:])
            requested_account.question_access = False
            db.session.commit()


if __name__ == "__main__":
    app.run()
