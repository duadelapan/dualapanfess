import io
import json
import os
import random
import re
from html import unescape

import requests
from flask import Flask
from flask import request, abort
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from googleapiclient import discovery
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, \
    ButtonsTemplate, URIAction, ImageMessage, QuickReply, QuickReplyButton, MessageAction, JoinEvent
from sqlalchemy import or_
import tictactoe
import util
from google_search import search_google
from question import add_question, add_answer, delete_all, delete_question, get_question_str, search_question, \
    get_changed_questions
from tables import db, LineAccount, LineGroup, Access
from twitter_bot import tweet, test_tweet
from webhook_app import webhook_app

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
MY_LINE_ID = "Ub2cd3e3460664f1ea60deab2b3863c55"


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
    group_access = Access.query.get(4)
    if not group_access.accessible:
        if event.source.type == "group":
            line_bot_api.leave_group(event.source.group_id)
        else:
            line_bot_api.leave_room(event.source.room_id)
    else:
        if event.source.type == "group":
            name = line_bot_api.get_group_summary(event.source.group_id).group_name
        else:
            name = ""
        message = f"Halo {name}!\n\n" \
                  "Untuk daftar command, ketik /command\n\n" \
                  "28 Menfess Twitter Bot:\n" \
                  "Keywords: \n" \
                  "/tweet28fess\n\n" \
                  "Untuk fess tweet, bisa menggunakan command di atas atau chat langsung dengan kata kunci \n" \
                  "dupan!\n\n" \
                  "FOLLOW\n" \
                  "https://twitter.com/28FESS?s=20\n\n" \
                  "/bye to make this bot leave"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    account = LineAccount.query.filter_by(account_id=event.source.user_id).first()
    if account:
        if account.img_soon and account.tweet_phase == "img":
            if util.check_timeout(account.last_tweet_req, 300):
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
            account.last_tweet_req = util.datetime_now_string()
            db.session.commit()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    access = Access.query.get(1)
    all_access = Access.query.get(2)
    lagi_pelajaran_ipa = Access.query.get(3)
    accessible = access.accessible
    user_message = event.message.text
    user_message_lower = user_message.lower()
    reply_token = event.reply_token
    account = LineAccount.query.filter_by(account_id=event.source.user_id).first()

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

    if event.source.type == "group":
        group = LineGroup.query.get(event.source.group_id)
        if not group:
            group = LineGroup(id=event.source.group_id)
            group.name = line_bot_api.get_group_summary(group.id).group_name
            db.session.add(group)
            db.session.commit()
        if user_message_lower == "/bye":
            line_bot_api.leave_group(group.id)
            return
        if (account.tic_tac_toe and account.tic_tac_toe.is_playing) or user_message_lower == "/tictactoe":
            if account.tic_tac_toe_id == group.id or not account.tic_tac_toe:
                if tictactoe.play(group.id, account, user_message, reply_token, line_bot_api):
                    return
    elif event.source.type == "room":
        if user_message_lower == "/bye":
            line_bot_api.leave_group(event.source.room_id)
            return
        if (account.tic_tac_toe and account.tic_tac_toe.is_playing) or user_message_lower == "/tictactoe":
            if account.tic_tac_toe_id == event.source.room_id or not account.tic_tac_toe:
                if tictactoe.play(event.source.room_id, account, user_message, reply_token, line_bot_api):
                    return
    if (account.tic_tac_toe and account.tic_tac_toe.is_playing and account.tic_tac_toe_id == account.account_id) \
            or user_message_lower == "/tictactoecomp":
        tictactoe.play(account.account_id, account, user_message, reply_token, line_bot_api, True)
        return

    if account.is_add_question:
        account.is_add_question = False
        db.session.commit()
        add_answer(account.question_id, user_message)
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(get_question_str(account.question_id))
        )
    elif "dupan!" in user_message_lower:
        account.tweet_phase = "img ask"
        account.next_tweet_msg = util.filter_tweet(user_message)
        account.last_tweet_req = util.datetime_now_string()
        db.session.commit()
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage("Want to attach an image?\n\n"
                            f"/yes {get_emoji_str('0x1000A5')} or /no {get_emoji_str('0x1000A6')}\n"
                            "/canceltweet to cancel ❌",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction("YES", "/yes")),
                                QuickReplyButton(action=MessageAction("NO", "/no")),
                                QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                            ]))
        )
    elif user_message_lower == "snmptn":
        day, hour, minute, second = util.get_delta_time(2021, 3, 22, 15)
        if day*24 + hour < 100:
            countdown = f"{day*24 + hour} jam {minute} menit {second} detik lagi"
        else:
            countdown = f"{day} hari {hour} jam {minute} menit {second} detik lagi."
        line_bot_api.reply_message(
            reply_token,
            TemplateSendMessage(
                alt_text=f"Pengumuman SNMPTN\n"
                         f"🕒 {countdown} 😲",
                template=ButtonsTemplate(
                    thumbnail_image_url='https://statik.tempo.co/data/2019/12/01/id_893849/893849_720.jpg',
                    title='Pengumuman SNMPTN',
                    text=f"{countdown}.",
                    actions=[
                        URIAction(
                            label='Live Countdown',
                            uri='https://snmptn.arsaizdihar.com/'
                        )
                    ]
                )
            ))
    elif user_message_lower == "sbmptn":
        day, hour, minute, second = util.get_delta_time(2021, 4, 12)
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"SBMPTN\n"
                                 f"{get_emoji_str('0x100071')}"
                                 f"{day} hari {hour} jam "
                                 f"{minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
    elif user_message_lower == "ppkb":
        day, hour, minute, second = util.get_delta_time(2021, 3, 26, 13)
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"PENGUMUMAN PPKB\n"
                                 f"{get_emoji_str('0x100071')}"
                                 f"{day} hari {hour} jam "
                                 f"{minute} menit {second} detik lagi {get_emoji_str('0x100032')}"))
    elif user_message_lower == "/testtweet":
        test = test_tweet()
        if test:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("success")
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("fail")
            )
    elif re.match("/youtube +[^ ]", user_message_lower):
        query = re.sub("/youtube +([^ ])", r"\1", user_message, flags=re.IGNORECASE)
        title, url = get_youtube_url(query)
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"{title}\n{url}")
        )

    elif user_message_lower == "/meme":
        response = requests.get('https://meme-api.herokuapp.com/gimme')
        url = response.json()['url']
        line_bot_api.reply_message(
            reply_token,
            ImageSendMessage(original_content_url=url, preview_image_url=url)
        )
    elif user_message_lower.startswith("/number"):
        if user_message_lower == "/number":
            message = "Keywords: \n" \
                      "- /number (number)\n" \
                      "- /number/random"
        else:
            res_type = random.choice(('math', 'trivia'))
            req = user_message_lower[7:]
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
            reply_token,
            TextSendMessage(text=message)
        )

    elif user_message_lower == "/cat":
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        data = response.json()
        url = data[0]['url']
        line_bot_api.reply_message(
            reply_token,
            ImageSendMessage(url, url)
        )
    elif user_message_lower == "/tweet28fess":
        account.tweet_phase = "from"
        account.next_tweet_msg = "from: "
        account.last_tweet_req = util.datetime_now_string()
        db.session.commit()
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(f"from: \n\n/canceltweet to cancel ❌",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                            ]))
        )
    elif user_message_lower == "/tumbal" and event.source.type == "group":
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
            reply_token,
            TextSendMessage("Daftar Tumbal" + "\n" + group.data)
        )
        db.session.commit()
    elif user_message_lower == "/tumbalkelar" and event.source.type == "group":
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
                    reply_token,
                    messages=messages
                )
                group.data = ""
                group.phase = ""
                group.member_ids = ""
                db.session.commit()
    elif re.match("/google +[^ ]", user_message_lower):
        query = re.sub("/google +([^ ])", r"\1", user_message, flags=re.IGNORECASE)
        results = search_google(query)
        message = ""
        for result in results:
            message += f"{result['title']}\n{result['description']}\n{result['link']}\n\n"
        message = message[:-2]
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(message)
        )
    elif user_message_lower.startswith("/pilih ") and ", " in user_message_lower:
        pilihan = user_message[7:].split(", ")
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(random.choice(pilihan))
        )
    elif user_message_lower.startswith("/kerangajaib "):
        random.seed(user_message_lower)
        random_range = random.random()
        if random_range <= 0.4:
            answer = "iya"
        elif random_range <= 0.8:
            answer = "tidak"
        elif random_range <= 0.98:
            answer = "bisa jadi"
        else:
            answer = "siapa lu nanya2"
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(answer)
        )
        random.seed()
    elif re.match("/balik +[^ ]", user_message_lower):
        message = " ".join("".join(reversed(x)) for x in
                           re.sub("/balik +([^ ])", r"\1", user_message, flags=re.IGNORECASE).split(" "))
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(message)
        )
    elif re.match("/mirror +[^ ]", user_message_lower):
        trans = str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
                              'ɐqɔpǝɟɓɥᴉſʞๅɯuodbɹsʇnʌʍxʎzⱯꓭꓛꓷƎꓞꓨHIſꓘꓶWNOꓒῸꓤSꓕꓵꓥMX⅄Z')
        message = re.sub("/mirror +([^ ])", r"\1", user_message, flags=re.IGNORECASE).translate(trans)

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(message)
        )
    elif user_message_lower == "/balik":
        if account.tweet_phase == "balik":
            account.tweet_phase = ""
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Balik mode off")
            )
        else:
            account.tweet_phase = "balik"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Balik mode on")
            )
        db.session.commit()
    elif user_message_lower == "/mirror":
        if account.tweet_phase == "mirror":
            account.tweet_phase = ""
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Mirror mode off")
            )
        else:
            account.tweet_phase = "mirror"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Mirror mode on")
            )
        db.session.commit()
    elif re.match("(/addq|/addqa|/addqs) +[^ ]", user_message_lower):
        if ((account.ipa_access or account.ips_access) and accessible) or account.is_superuser or account.is_adder:
            account.is_add_question = True
            groups = re.match(r"(/addq|/addqa|/addqs) +([^ ][\s\S]+)", user_message, flags=re.IGNORECASE)
            query = groups.group(1).lower()
            is_ipa = query == "/addqa"
            is_ips = query == "/addqs"
            if not is_ipa and not is_ips:
                is_ipa = True
                if not lagi_pelajaran_ipa.accessible:
                    is_ips = True
            question = groups.group(2)
            question_id = add_question(question, is_ipa, is_ips)
            if question_id:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(f"Question Added. ID: {question_id}\nAnswer: ")
                )
                account.question_id = question_id
                db.session.commit()
            else:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(f"Question already exist.\n{search_question(question, is_ipa, is_ips)}")
                )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Access Denied.")
            )

    elif re.match(r"/addans +[\d]+ +[^ ]", user_message_lower):
        if ((account.ipa_access or account.ips_access) and accessible) or account.is_superuser or account.is_adder:
            groups = re.match(r"/addans +([\d]+) +([^ ][\s\S]+)", user_message, flags=re.IGNORECASE)
            question_id = groups.group(1)
            answer = groups.group(2)
            if add_answer(question_id, answer, True):
                message = get_question_str(question_id)
            else:
                message = "ID invalid"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Access Denied.")
            )
    elif user_message_lower == "/soalganti":
        if ((account.ipa_access or account.ips_access) and accessible) or account.is_superuser or all_access.accessible or account.is_adder:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(get_changed_questions(account.ipa_access, account.ips_access, account.is_superuser))
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Access Denied.")
            )

    elif re.match("(/searchq|/sq) +[^ ]", user_message_lower):
        if ((account.ipa_access or account.ips_access) and accessible) or account.is_superuser or all_access.accessible or account.is_adder:
            message = search_question(re.sub("(/searchq|/sq) +([^ ])", r"\2", user_message, flags=re.IGNORECASE)
                                      , account.ipa_access, account.ips_access, account.is_superuser)
            if len(message) > 5000:
                message = "Too many results."
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Access Denied.")
            )

    elif re.match(r"/getq +\d+", user_message_lower):
        if ((account.ipa_access or account.ips_access) and accessible) or account.is_superuser or all_access.accessible or account.is_adder:
            question_id = re.sub(r"/getq +(\d+)", r"\1", user_message)
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(get_question_str(question_id))
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("Access Denied.")
            )

    else:
        if account:
            phase = account.tweet_phase
            if phase and phase == "balik":
                message = " ".join("".join(reversed(x)) for x in user_message.split(" "))
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(message)
                )
            if phase == "mirror":
                trans = str.maketrans('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                      'ɐqɔpǝɟɓɥᴉſʞๅɯuodbɹsʇnʌʍxʎzⱯꓭꓛꓷƎꓞꓨHIſꓘꓶWNOꓒῸꓤSꓕꓵꓥMX⅄Z')
                message = user_message.translate(trans)
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(message)
                )
            elif phase:
                if user_message_lower == "/canceltweet":
                    util.clear_account_tweet_data(account)
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage("Tweet Cancelled")
                    )
                else:
                    if util.check_timeout(account.last_tweet_req, 300):
                        now = util.datetime_now_string()
                        account.last_tweet_req = now
                        if phase == "from":
                            account.tweet_phase = "to"
                            account.next_tweet_msg += user_message + "\nto: "
                            line_bot_api.reply_message(
                                reply_token,
                                TextSendMessage(f"to: \n\n/canceltweet to cancel ❌",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "to":
                            account.tweet_phase = "text"
                            account.next_tweet_msg += user_message + "\n"
                            line_bot_api.reply_message(
                                reply_token,
                                TextSendMessage(f"message: \n\n/canceltweet to cancel ❌",
                                                quick_reply=QuickReply(items=[
                                                    QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                ]))
                            )
                        if phase == "text":
                            msg = util.filter_tweet(account.next_tweet_msg + user_message)
                            account.tweet_phase = "img ask"
                            account.next_tweet_msg = msg
                            line_bot_api.reply_message(
                                reply_token,
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
                            if user_message_lower == "/yes":
                                account.img_soon = True
                                account.tweet_phase = "img"
                                line_bot_api.reply_message(
                                    reply_token,
                                    TextSendMessage("Send an image within 5 min.\n\n"
                                                    f"/canceltweet to cancel ❌",
                                                    quick_reply=QuickReply(items=[
                                                        QuickReplyButton(
                                                            action=MessageAction("CANCEL", "/canceltweet"))
                                                    ]))
                                )
                            elif user_message_lower == "/no":
                                account.tweet_phase = "confirm"
                                line_bot_api.reply_message(
                                    reply_token,
                                    TextSendMessage("❗❗CONFIRMATION❗❗\n\n"
                                                    f"{account.next_tweet_msg}\n\n"
                                                    f"/send to tweet ✉️\n"
                                                    f"/canceltweet to cancel ❌",
                                                    quick_reply=QuickReply(items=[
                                                        QuickReplyButton(action=MessageAction("SEND", "/send")),
                                                        QuickReplyButton(action=MessageAction("CANCEL", "/canceltweet"))
                                                    ]))
                                )
                        if phase.startswith("confirm") and user_message_lower == "/send":
                            if account.img_soon:
                                msg_media_id = phase.split(" ")[-1]
                                pic = line_bot_api.get_message_content(msg_media_id)
                                file = io.BytesIO(pic.content)
                                url = tweet(account.next_tweet_msg, file, account=account)
                                file.close()
                            else:
                                url = tweet(account.next_tweet_msg, account=account)
                            util.clear_account_tweet_data(account)
                            if url.startswith("https"):
                                account.last_tweet = now
                                message = f"Tweet Posted.\nurl: {url}"
                            else:
                                message = url
                            line_bot_api.reply_message(
                                reply_token,
                                TextSendMessage(message)
                            )
                    else:
                        util.clear_account_tweet_data(account)
                db.session.commit()

    if account.account_id == MY_LINE_ID:
        if user_message_lower.startswith("/getid "):
            search_name = user_message[7:]
            accounts = LineAccount.query.filter(LineAccount.name.ilike(f"%{search_name}%"))
            if accounts:
                msg_ids = '\n'.join([search_account.account_id for search_account in accounts])
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(f"ID:\n{msg_ids}")
                )
            else:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage("No account found.")
                )
        elif user_message_lower.startswith("/addacca "):
            requested_account = LineAccount.query.get(user_message[9:])
            requested_account.ipa_access = True
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(f"{requested_account.name} added to MIPA access")
            )

        elif user_message_lower.startswith("/addaccs "):
            requested_account = LineAccount.query.get(user_message[9:])
            requested_account.ips_access = True
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(f"{requested_account.name} added to IPS access")
            )

        elif user_message_lower.startswith("/removeacca "):
            requested_account = LineAccount.query.get(user_message[12:])
            requested_account.ipa_access = False
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(f"{requested_account.name} removed from MIPA access")
            )

        elif user_message_lower.startswith("/removeaccs "):
            requested_account = LineAccount.query.get(user_message[12:])
            requested_account.ips_access = False
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(f"{requested_account.name} removed from IPS access")
            )

        elif user_message_lower.startswith("/delq "):
            question_id = user_message_lower[6:]
            if question_id.isnumeric():
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(delete_question(question_id))
                )

        elif user_message_lower == "/delqall":
            delete_all()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("All Question deleted")
            )

        elif user_message_lower == "/allacc":
            all_accounts = LineAccount.query.filter(or_(LineAccount.ipa_access, LineAccount.ips_access)).all()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("\n".join([acc.name for acc in all_accounts]))
            )

        elif user_message_lower == "/allacca":
            all_accounts = LineAccount.query.filter(LineAccount.ipa_access).all()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("\n".join([acc.name for acc in all_accounts]))
            )

        elif user_message_lower == "/allaccs":
            all_accounts = LineAccount.query.filter(LineAccount.ips_access).all()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage("\n".join([acc.name for acc in all_accounts]))
            )

        elif user_message_lower == "/qaccess":
            access.accessible = not access.accessible
            message = "All access enabled" if access.accessible else "All access disabled"
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )

        elif user_message_lower == "/qallaccess":
            all_access.accessible = not all_access.accessible
            message = "All access for everyone enabled" if all_access.accessible else "All access for everyone disabled"
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )
        elif user_message_lower == "/ipamode":
            lagi_pelajaran_ipa.accessible = not lagi_pelajaran_ipa.accessible
            message = "MIPA enabled" if lagi_pelajaran_ipa.accessible else "MIPA disabled"
            db.session.commit()
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )
        elif user_message_lower == "/joingroup":
            group_access = Access.query.get(4)
            group_access.accessible = not group_access.accessible
            db.session.commit()
            message = "Join group enabled" if group_access.accessible else "Join group disabled"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(message)
            )


if __name__ == "__main__":
    app.run()
