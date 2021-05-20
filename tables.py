from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class LineAccount(db.Model):
    account_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(20))
    tweets = relationship("TweetPost", back_populates="sender_line")
    last_tweet = db.Column(db.String(100))
    img_soon = db.Column(db.Boolean, default=False)
    last_tweet_req = db.Column(db.String(100))
    next_tweet_msg = db.Column(db.Text)
    tweet_phase = db.Column(db.String(50))
    is_add_question = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer)
    ipa_access = db.Column(db.Boolean, default=False)
    ips_access = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    is_adder = db.Column(db.Boolean, default=False)
    tic_tac_toe_id = db.Column(db.String(50), db.ForeignKey("tic_tac_toe.id"))
    tic_tac_toe = relationship("TicTacToe", back_populates="players")


class LineGroup(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50))
    phase = db.Column(db.String(50))
    data = db.Column(db.Text)
    member_ids = db.Column(db.Text)


class TwitterAccount(db.Model):
    account_id = db.Column(db.String(50), primary_key=True)
    tweets = relationship("TweetPost", back_populates="sender_twitter")
    last_tweet = db.Column(db.String(100))
    img_soon = db.Column(db.Boolean, default=False)
    last_tweet_req = db.Column(db.String(100))
    next_tweet_msg = db.Column(db.Text)
    tweet_phase = db.Column(db.Text)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    is_changed = db.Column(db.Boolean, default=False)
    q_ipa = db.Column(db.Boolean, default=False)
    q_ips = db.Column(db.Boolean, default=False)


class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accessible = db.Column(db.Boolean, default=False)


class TweetPost(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    sender_line_id = db.Column(db.String(50), db.ForeignKey("line_account.account_id"))
    sender_line = relationship("LineAccount", back_populates="tweets")
    sender_twitter_id = db.Column(db.String(50), db.ForeignKey("twitter_account.account_id"))
    sender_twitter = relationship("TwitterAccount", back_populates="tweets")
    time = db.Column(db.String(100))
    text = db.Column(db.Text)


class TicTacToe(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    board = db.Column(db.LargeBinary)
    is_playing = db.Column(db.Boolean, default=True)
    players = relationship("LineAccount", back_populates="tic_tac_toe")
    first_player = db.Column(db.String(50))


class ReplyToken(db.Model):
    token = db.Column(db.String(100), primary_key=True)


class Image(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    image = db.Column(db.LargeBinary)


