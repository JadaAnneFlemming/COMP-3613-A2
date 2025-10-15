from App.models.accolade import Accolade
from App.database import db

def award_accolades(student):

    milestones = [10, 20, 50]
    earned = []

    for accolade in student.accolades:
        earned.append(accolade.milestone)

    new_accs = []

    for m in milestones:
        if student.total_hours >= m and m not in earned:
            acc = Accolade(milestone=m, student=student)
            db.session.add(acc)
            new_accs.append(acc)

    return new_accs