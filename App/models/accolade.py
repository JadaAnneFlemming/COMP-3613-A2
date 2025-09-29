from App.database import db
from datetime import datetime


class Accolade(db.Model):
    __tablename__ = 'accolades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))

    milestone = db.Column(db.Integer, nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="accolades")

    def __repr__(self):
        return f"<Accolade {self.milestone} Hours for Student ID {self.student_id}>"


    def format_awarded_time(self):
        if self.awarded_at:
            return self.awarded_at.strftime("%Y-%m-%d %H:%M")
        return None
    
    def milestone_name(self):
        if self.milestone == 10:
            return "Bronze"
        elif self.milestone == 20:
            return "Silver"
        elif self.milestone == 50:
            return "Gold"
        else:
            return f"{self.milestone} hours"




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