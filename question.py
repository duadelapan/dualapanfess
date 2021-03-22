from tables import db, Question
from sqlalchemy import func


def search_question(keyword, ipa=False, ips=False, superuser=False):
    look_for = f"%{keyword}%"
    if not superuser:
        if ipa:
            questions = Question.query.filter(Question.question.ilike(look_for)).filter_by(q_ipa=ipa).all()
        else:
            questions = Question.query.filter(Question.question.ilike(look_for)).filter_by(q_ips=ips).all()
    else:
        questions = Question.query.filter(Question.question.ilike(look_for)).all()
    if questions:
        message = ""
        for question in questions:
            message += f"ID: {question.id}\n{question.question}\nANS:\n{question.answer}\n\n"
        return message
    return f"keyword: {keyword}\nNo question found"


def get_question_str(question_id):
    question = Question.query.get(question_id)
    if question:
        return f"ID: {question.id}\n{question.question}\nANS:\n{question.answer}"
    return "Invalid ID"


def add_question(question, ipa=False, ips=False):
    questions = Question.query.filter(Question.question.ilike(f"%{question}%")).first()
    if not questions:
        new_question = Question(question=question)
        new_question.q_ipa = ipa
        new_question.q_ips = ips
        db.session.add(new_question)
        db.session.commit()
        return new_question.id
    return False


def add_answer(question_id, answer, change=False):
    question = Question.query.get(question_id)
    if question:
        question.answer = answer
        if change:
            question.is_changed = True
        db.session.commit()
        return True
    return False


def delete_all():
    for question in Question.query.all():
        db.session.delete(question)
    db.session.connection().execute("ALTER SEQUENCE question_id_seq RESTART WITH 1;")
    db.session.commit()


def delete_question(question_id):
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        reset_id = db.session.query(func.max(Question.id)).scalar()
        if reset_id:
            reset_id += 1
        else:
            reset_id = 1
        db.session.connection().execute(f"ALTER SEQUENCE question_id_seq RESTART WITH {reset_id};")
        db.session.commit()
        return question.question + "\nDeleted."
    return False


def get_changed_questions(ipa=False, ips=False, superuser=False):
    if not superuser:
        if ipa:
            questions = Question.query.filter_by(is_changed=True, q_ipa=ipa).all()
        else:
            questions = Question.query.filter_by(is_changed=True, q_ips=ips).all()
    else:
        questions = Question.query.filter_by(is_changed=True).all()
    if questions:
        message = "CHANGED QUESTIONS\n\n"
        for question in questions:
            message += f"ID: {question.id}\n{question.question}\nANS:\n{question.answer}\n\n"
        if len(message) > 5000:
            message = "CHANGED QUESTIONS\n\n"
            for question in questions:
                message += f"ID: {question.id}\n"
        return message
    return "No question changed."
