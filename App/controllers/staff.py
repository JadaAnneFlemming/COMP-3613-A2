from App.models import Staff
from App.models import Student
from App.models import HourLog

from App.controllers.accolade import award_accolades

from App.database import db
from datetime import datetime

def log_hours(staff_id, student_id, hours):
    staff = Staff.query.get(staff_id)
    student = Student.query.get(student_id)
    if staff and student and hours > 0:
        log = HourLog(hours=hours, student=student, staff=staff, status="confirmed", reviewed_at=datetime.utcnow())
        db.session.add(log)
        student.total_hours += hours
        award_accolades(student)
        db.session.commit()
        return log
    return None


def get_pending_logs():
    return HourLog.query.filter_by(status="requested").all()

def confirm_hours(staff_id, log_id):
    staff = Staff.query.get(staff_id)
    log = HourLog.query.get(log_id)
    if log and staff and log.status == "requested":
        log.status = "confirmed"
        log.staff = staff
        log.reviewed_at = datetime.utcnow()
        log.student.total_hours += log.hours
        award_accolades(log.student)
        db.session.commit()
        return log
    return None


def deny_hours(staff_id, log_id):
    staff = Staff.query.get(staff_id)
    log = HourLog.query.get(log_id)
    if staff and log and log.status == "requested":
        log.status = "denied"
        log.staff = staff
        log.reviewed_at = datetime.utcnow()
        db.session.commit()
        return log
    return None

def get_staff(staff_id):
    return Staff.query.get(staff_id)
