from tables import db, Question


def search_question(keyword):
    look_for = f"%{keyword}%"
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


def add_question(question):
    questions = Question.query.filter(Question.question.ilike(f"%{question}%")).first()
    if not questions:
        new_question = Question(question=question)
        db.session.add(new_question)
        db.session.commit()
        return new_question.id
    return False


def add_answer(question_id, answer):
    question = Question.query.get(question_id)
    if question:
        question.answer = answer
        db.session.commit()
        return True
    return False


def delete_all():
    for question in Question.query.all():
        db.session.delete(question)
    db.session.commit()


def delete_question(question_id):
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
        return True
    return False
