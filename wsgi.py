import click, pytest, sys
from flask.cli import with_appcontext, AppGroup

from App.database import db, get_migrate

from App.models.user import *
from App.models.student import *
from App.models.staff import *
from App.models.hour_log import *
from App.models.accolade import *


from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize )
from tabulate import tabulate

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)


# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database.")
def init():
    initialize()

    # Populating system with existing users

    students = [
        Student(username='alice', password='alicepass'), #ID 1
        Student(username='rob', password='robpass'), #ID 2
        Student(username='carol', password='carolpass'), #ID 3
        Student(username='dave', password='davepass'), #ID 4
        Student(username='eve', password='evepass'), #ID 5
        Student(username='frank', password='frankpass'), #ID 6
        Student(username='grace', password='gracepass'), #ID 7
        Student(username='heidi', password='heidipass'), #ID 8
        Student(username='ivan', password='ivanpass'), #ID 9
        Student(username='judy', password='judypass') #ID 10
    ]

    staff = [
        Staff(username='sally', password='sallypass'), #ID 11
        Staff(username='steve', password='stevepass'), #ID 12
        Staff(username='john', password='johnpass'), #ID 13
        Staff(username='laura', password='laurapass'), #ID 14
        Staff(username='mike', password='mikepass') #ID 15

    ]

    db.session.add_all(students + staff)
    db.session.commit()
   

    hours = [
        (staff[0], students[0], 10), # staff[0] is sally with ID 11, students[0] is alice with ID 1
        (staff[0], students[1], 15), # staff[0] is sally with ID 11, students[1] is rob with ID 2
        (staff[1], students[2], 20), # staff[1] is steve with ID 12, students[2] is carol with ID 3
        (staff[1], students[3], 12), # staff[1] is steve with ID 12, students[3] is dave with ID 4
        (staff[2], students[4], 18), # staff[2] is john with ID 13, students[4] is eve with ID 5
        (staff[2], students[5], 25), # staff[2] is john with ID 13, students[5] is frank with ID 6
        (staff[3], students[6], 8), # staff[3] is laura with ID 14, students[6] is grace with ID 7
        (staff[3], students[7], 16), # staff[3] is laura with ID 14, students[7] is heidi with ID 8
        (staff[4], students[8], 22)  # staff[4] is mike with ID 15, students[8] is ivan with ID 9
    ]

    for s, student, h in hours:
        log = HourLog(staff=s, student=student, hours=h, status="confirmed", reviewed_at=datetime.utcnow())
        db.session.add(log)
        student.total_hours += h  
        award_accolades(student)

    db.session.commit()
    print('Database intialized!')



"""---------------- General Commands ----------------"""

# Command to create a new student or staff account
# flask create <username> <password> <role>

@app.cli.command("create", help="Creates a new student or staff account (default: student).")
@click.argument("username", default="bob")
@click.argument("password", default="bobpass")
@click.argument("role", default="student")
def create_user_command(username, password, role):

    if role not in ['student', 'staff']:
        print("Invalid role! Must be 'student' or 'staff'.")
        return
        
    if User.query.filter_by(username=username).first():
        print("Username already exists!")
        return
        
    if role == 'student':
        new_user = Student(username=username, password=password)
    elif role == 'staff':
        new_user = Staff(username=username, password=password)

    db.session.add(new_user)
    db.session.commit()

    print(f"Created new {role} {username} with ID {new_user.id}!")



# Command to list all users of filter by role
# flask list
# flask list --type <role>

@app.cli.command("list", help="List all users in the system, or only those with a specific role.")
@click.option("--type", default="all", help="Roles to filter by: student, staff or all (default: all).")
def list_user_command(type):

    if type == "student":
        users = Student.query.all()
    elif type == "staff":
        users = Staff.query.all()
    else:
        users = User.query.all()

    
    if not users:
        print("No users found!")
        return
    
    table = []
    for u in users:
        table.append([u.id, u.username, u.role])

    print(tabulate(table, headers=["ID", "Username", "Role"], tablefmt="grid"))
    


"""---------------- User Commands ----------------"""
# Commands that can be used by all role types

user_cli = AppGroup('user', help='Commands available to all users.') 


# Command to view the student leaderboard
# flask user leaderboard

@user_cli.command("leaderboard", help="View student leaderboard ranked by total confirmed hours logged.")
def leaderboard_command():

    students = Student.query.order_by(Student.total_hours.desc()).all()
    table = []
    previous_hours = None
    rank = 0

    for student in students:
        if student.total_hours != previous_hours:
            rank += 1
            previous_hours = student.total_hours
        table.append([rank, student.username, student.total_hours])

    print("Student Leaderboard")
    print(tabulate(table, headers=["Rank", "Student", "Total Hours"], tablefmt="grid"))


app.cli.add_command(user_cli)



""" ----------------- Student Commands ----------------- """
# Commands that can be used by students only

student_cli = AppGroup('student', help='Commands available to students only.')

# Command to request hours
# flask student request-hours <student_id> <hours>

@student_cli.command("request-hours", help="Submit a request to log volunteer hours.")
@click.argument("student_id", type=int)
@click.argument("hours", type=int)
def request_hours_command(student_id, hours):

    student = get_student(student_id)

    if not student:
        print(f"Student with id {student_id} not found!")
        return
    
    if hours <= 0:
        print("Requested hours must be greater than zero!")
        return
    
    log = HourLog(hours=hours, student=student, status="requested")
    db.session.add(log)
    db.session.commit()

    print(f"Student {student.username} requested {hours} hours!")


# Command to view personal log (shows all hours requested/confirmed/denied for student)
# flask student view-log <student_id>

@student_cli.command("view-log", help="View all logged hours, including requested, confirmed, and denied requests.")
@click.argument("student_id", type=int)
def view_student_requests_command(student_id):

    student = get_student(student_id)

    if not student:
        print(f"Student with id {student_id} not found!")
        return
    
    logs = HourLog.query.filter_by(student=student).all()

    if not logs:
        print(f"No requested logs found for student {student.username}!")
        return
        
    table = []
    for log in logs:
        if log.staff:
            staff_name = log.staff.username
        else:
            staff_name = "pending"
    
        row = [log.id, log.hours, log.status, staff_name, log.format_created_time(), log.format_reviewed_time()]
        table.append(row)

    print(f"Hour Logs for {student.username}:")
    print(tabulate(table, headers=["Log ID", "Hours", "Status", "Confirmed By", "Requested At", "Reviewed At"], tablefmt="grid"))


# Command to view own accolades
# flask student view-accolades <student_id>

@student_cli.command("view-accolades", help="View all personal accolades earned.")
@click.argument("student_id", type=int)
def view_accolades_command(student_id):
    
    milestones = [10, 20, 50]

    student = get_student(student_id)

    if not student:
        print(f"Student with id {student_id} not found!")
        return
    
    accolades = []

    for m in milestones:
        for acc in student.accolades:
            if acc.milestone == m:
                accolades.append(acc)

    if not accolades:
        print(f"{student.username} has not earned any accolades yet!")
        return
    
    table = []
    for acc in accolades:
        row = [acc.milestone_name(), acc.milestone, acc.format_awarded_time()]
        table.append(row)

    
    print(f"Accolades for {student.username}")
    print(tabulate(table, headers=["Accolade", "Milestone", "Awarded At"], tablefmt="grid"))

        
app.cli.add_command(student_cli)


""" ----------------- Staff Commands ----------------- """
# Commands that can be used by staff only

staff_cli = AppGroup('staff', help='Commands available to staff only.')

# Command to log hours directly for a student (no previous request made)
# flask staff log-hours <staff_id> <student_id> <hours>

@staff_cli.command("log-hours", help="Log hours for a student directly.")
@click.argument("staff_id", type=int)
@click.argument("student_id", type=int)
@click.argument("hours", type=int)
def log_hours_command(staff_id, student_id, hours):

    staff = get_staff(staff_id)
    student = get_student(student_id)

    if not staff or not student:
        print(f"Invalid staff or student ID!")
        return
    
    log = HourLog(hours=hours, student=student, staff=staff, status="confirmed", reviewed_at=datetime.utcnow())
    db.session.add(log)
    student.total_hours += hours
    award_accolades(student)
   
    db.session.commit()

    print(f"{hours} hours has been logged for {student.username} by {staff.username}!")
    

# Command to view all outstanding requests from students
# flask staff view-all-requests

@staff_cli.command("view-all-requests", help="View all outstanding student requests.")
def view_all_requests_command():
    
    logs = HourLog.query.filter_by(status="requested").all()

    if not logs:
        print("No pending logs!")
        return
    
    table = []
    for log in logs:
        student_name = log.student.username
        row = [log.id, student_name, log.hours, log.status, log.format_created_time(), log.format_reviewed_time()]
        table.append(row)

    print(tabulate(table, headers=["Log ID", "Student", "Hours", "Status", "Requested At", "Reviewed At"], tablefmt="grid"))




# Command to confirm hours for a student request
# flask staff confirm-hours <staff_id> <log_id>
@staff_cli.command("confirm-hours", help="Confirm a student's request for hours.")
@click.argument("staff_id", type=int)
@click.argument("log_id", type=int)
def confirm_hours_command(staff_id, log_id):

    staff = get_staff(staff_id)
    log = get_log (log_id)

    if not staff or not log or log.status != 'requested':
        print(f"Invalid staff id or log!")
        return
    
    log.status = "confirmed"
    log.staff = staff
    log.reviewed_at = datetime.utcnow()
    log.student.total_hours += log.hours
    award_accolades(log.student)
   
    db.session.commit()
   
    print(f"Confirmed {log.hours} hours for {log.student.username} by {staff.username}!")




# Command to deny hours for a student request
# flask staff deny-hours <staff_id> <log_id>
@staff_cli.command("deny-hours", help="Deny a student's request for hours.")
@click.argument("staff_id", type=int)
@click.argument("log_id", type=int)
def deny_hours_command(staff_id, log_id):

    staff = get_staff(staff_id)
    log = get_log (log_id)

    if not staff or not log or log.status != 'requested':
        print(f"Invalid staff id or log!")
        return
    
    log.status = "denied"
    log.staff = staff
    log.reviewed_at = datetime.utcnow()
    db.session.commit()

    print(f"Denied {log.hours} hours for {log.student.username} by {staff.username}!")

app.cli.add_command(staff_cli)



'''
Test Commands
'''

test = AppGroup('test', help='Testing commands.') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)