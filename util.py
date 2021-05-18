import re
from datetime import datetime, timedelta

from tables import db

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def last_index(iterable, element):
    try:
        index = list(reversed(iterable)).index(element)
    except ValueError:
        return None
    return len(iterable) - index - 1


def filter_tweet(text):
    return re.sub(r"(^|[^\w$@])(@|#)([\w]+)", r"\1\2.\3", text)


def get_id_from_link(link):
    return int(link[link.index('status/') + 7:])


def check_timeout(then, sec):
    then_datetime = datetime.strptime(then, TIME_FORMAT)
    now = datetime.utcnow()
    return (now - then_datetime).total_seconds() <= sec


def datetime_now_string():
    return datetime.utcnow().strftime(TIME_FORMAT)


def get_delta_time(year, month, day=0, hour=0):
    now = datetime.utcnow()
    now = now + timedelta(hours=7)
    request = datetime(year=year, month=month, day=day, hour=hour)
    delta = request - now
    day = delta.days
    clock = str(delta).split(", ")[-1]
    hour, minute, second = clock.split(':')
    second = second.split('.')[0]
    return int(day), int(hour), int(minute), int(second)


def clear_account_tweet_data(account):
    account.tweet_phase = ""
    account.next_tweet_msg = ""
    account.last_tweet_req = ""
    account.img_soon = False
    db.session.commit()
