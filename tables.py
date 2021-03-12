from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class LineAccount(db.Model):
    account_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(20))
    last_tweet = db.Column(db.String(100))
    img_soon = db.Column(db.Boolean, default=False)
    last_tweet_req = db.Column(db.String(100))
    next_tweet_msg = db.Column(db.Text)
    tweet_phase = db.Column(db.String(50))
    is_add_question = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer)
    question_access = db.Column(db.Boolean, default=False)


class LineGroup(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50))
    phase = db.Column(db.String(50))
    data = db.Column(db.Text)
    member_ids = db.Column(db.Text)


class TwitterAccount(db.Model):
    account_id = db.Column(db.String(50), primary_key=True)
    last_tweet = db.Column(db.String(100))
    img_soon = db.Column(db.Boolean, default=False)
    last_tweet_req = db.Column(db.String(100))
    next_tweet_msg = db.Column(db.Text)
    tweet_phase = db.Column(db.Text)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
