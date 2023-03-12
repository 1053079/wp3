import ast
import os

from os import environ, path
from dotenv import load_dotenv

from flask import (Flask, 
                  render_template, 
                  request, 
                  session, 
                  redirect, 
                  url_for, 
                  json, 
                  jsonify, 
                  flash
                  ) 

# from flask_login import (login_manager, 
#                         login_url, 
#                         login_user, 
#                         login_required, 
#                         set_login_view
#                         ) 

from flask_security import (Security, 
                           auth_required, 
                           login_user, 
                           logout_user, 
                           login_required, 
                           roles_required, 
                           roles_accepted
                           )


from lib.login import DB, datastore
from lib.student import StudentManagement
from lib.teacher import TeacherManagement
from lib.klas import ClassManagement
from lib.meeting import MeetingManagement
from lib.presence import PresenceManagement

# no touchy
projpath = path.join(path.dirname(__file__), '.env')
load_dotenv(projpath)

# Flask server
LISTEN_ALL = "0.0.0.0"
FLASK_IP = LISTEN_ALL
FLASK_PORT = 81
FLASK_DEBUG = True
#FLASK_RUN_CERT = "adhoc"

# Flask config
app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URI')
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login.html'
app.config["SECURITY_PASSWORD_SALT"] = environ.get('PW_SALT')

# Flask_security
DB.init_app(app)
Security(app, datastore)

# Database cnx
DB_FILE = os.path.join(app.root_path, "databases", "demo_data.db")

studentdb = StudentManagement(DB_FILE)
teacherdb = TeacherManagement(DB_FILE)
classdb = ClassManagement(DB_FILE)
meetingdb = MeetingManagement(DB_FILE)
presencedb = PresenceManagement(DB_FILE)

# routes
# @app.before_request
# def check_login():
#     if request.endpoint not in ["index","show_login", "handle_login"]:
#         if not session.get("logged_in"):
#             return redirect(url_for('show_login'))

# Main route
@app.route("/index")
def index():
     return render_template("index.html", title=index)

@app.route("/", methods=["GET","POST"])
@auth_required()
def link():
    match request.method:
        case 'GET':
            teacher_list = teacherdb.get_teacher()
    return render_template('link.html', teachers=teacher_list)

@app.route("/test-ajax.html", methods = ['GET'])
def testajax():
    return render_template("test-ajax.html")

@app.route("/base")

def base():
    return render_template("base.html")

# Url for QR Code scanning
@app.route('/QR')
def qr():
    return render_template("QRscan.html")

@app.route('/meeting')
@auth_required()
def meeting():
    return render_template('meeting_list.html')

@app.route('/api/meeting')
def api_meeting():
    meeting_list = meetingdb.get_all_meetings()
    print(meeting_list)

    return json.jsonify({
        'meetings': meeting_list
    })

@app.route('/meeting/new')
@auth_required()
def creat_meeting():
    teacher_list = teacherdb.get_teacher()
    class_list = classdb.get_class()
    
    return render_template('create_meeting.html', teachers=teacher_list, classes=class_list)

@app.post('/meeting/new') # shortcut voor methods = ["POST"]
@auth_required()
def meeting_post():
    meeting_name = str(request.form.get('meeting_name'))
    meeting_date = request.form.get('meeting_date')
    meeting_start_time = request.form.get('meeting_start_time')
    meeting_end_time = request.form.get('meeting_end_time')
    meeting_location = str(request.form.get('meeting_location'))
    meeting_teacher = str(request.form.getlist('meeting_teacher'))
    meeting_classes = str(request.form.getlist('meeting_class')).replace("[", "").replace("]", "")
    meeting_students = str(studentdb.get_students_by_class(meeting_classes))
    meeting_students2 = studentdb.get_students_by_class(meeting_classes)
    print(meeting_date)
    print(meeting_start_time)
    print(meeting_end_time)

    meetingdb.add_meeting(
        meeting_name,
        meeting_date,
        meeting_start_time,
        meeting_end_time,
        meeting_location,
        meeting_teacher,
        meeting_students,
        meeting_students2)

    flash("Meeting toegevoegd!", "info")
    return redirect(url_for('meeting'))

@app.route('/meeting/<meetingId>', methods=["GET", "PUT", "PATCH", "DELETE"])
@auth_required()
def meetingid(meetingId):
    match request.method:
        case 'GET':
            meeting_info = meetingdb.get_meeting(meetingId)
            student_list = ast.literal_eval(meeting_info[0]["student"])

            return render_template('meetingid.html', meetingId=meetingId, meeting_info=meeting_info, student_list=student_list)
        case 'POST':
             meeting_info = meetingdb.get_meeting(meetingId)
             return redirect('QRgen', meetingId=meetingId)
        case 'PUT':
            print("PUT")
        case 'PATCH':
            json_data = request.get_json()
            presencedb.update_presence(json_data)
            return json.jsonify()

@app.route('/api/<meetingId>')
def api_get_meeting(meetingId):

    presence_list = presencedb.get_presence(meetingId)

    return json.jsonify({
        'presence_list': presence_list
    })

@app.route('/api/class/json', methods=["GET"])
def api_get_docentmeeting():

    docent_meeting = meetingdb.get_all_meetings()
    print(docent_meeting)

    return json.jsonify({
        'meeting_info' : docent_meeting, 
    })

@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

@app.route('/checkin/<meetingId>', methods=["GET", "POST"])
def checkin_id(meetingId):
    match request.method:
        case 'GET':
         meeting_list = meetingdb.get_meeting(meetingId)
         return render_template('checkin.html', meetingId=meetingId, meetings=meeting_list)
        case 'POST':
         # placeholder #
         return render_template('checkin.html', meetingId=meetingId, meetings=meeting_list)

@app.route('/meeting/showForTeacher/<teacherId>', methods=["GET"])
@auth_required()

def meetingforteacher():
    match request.method:
        case 'GET':
            return render_template('meetingid.html')

@app.route('/api/student/<studentId>')
def api_get_student_presence(studentId):
    p_s_list = presencedb.get_presence_student(studentId)

    return jsonify({
        'presence' : p_s_list
    })

@app.route('/student')
@auth_required()
def student():
    return render_template('student.html')

@app.post('/student') # shortcut voor methods = ["POST"]
def student_post():
    return render_template('student.html')
   
@app.route('/student/<studentId>', methods=["GET", "DELETE"])
def studentid(studentId):
    return render_template('studentid.html')

@app.route('/api/student')
def api_get_students():
    s_list = studentdb.get_student_json()
    #print(s_list)
    # ik weet niet wat ik aan het doen ben, help
    #return json.dumps(s_list)
    return jsonify({ # oke, mooi. wat doe ik nu hier mee?
        'studenten' : s_list
    })

def studentid():
    match request.method:
        case 'GET':
            return render_template('studentid.html')
        case 'DELETE':
            print("DELETE")

@app.route('/api/teacher')
def api_get_teachers():
    t_list = teacherdb.get_teacher_json()
    #print(t_list)

    return jsonify({
        'docenten' : t_list
    })

@app.route('/teacher')
@auth_required()
def teacher():
    t_list = teacherdb.get_teacher()
    return render_template('teacher.html', teachers=t_list)

@app.post('/teacher') # shortcut voor methods = ["POST"]
def teacher_post():
    return render_template('teacher.html')

@app.route('/teacher/<teacherId>', methods=["GET", "PUT", "DELETE"])
def teacherid():
    match request.method:
        case 'GET':
            return render_template('teacherid.html')
        case 'PUT':
            print("PUT")
        case 'DELETE':
            print("DELTE")

@app.route('/api/klas')
def api_get_class():
    class_list = classdb.get_class()
    #print(class_list)

    return jsonify({
        'klassen' : class_list
    })

@app.route('/class')
def studentclass():
    class_list = classdb.get_class()
    return render_template('class.html', classes=class_list)

@app.post('/class') # shortcut voor methods = ["POST"]
def studentclass_post():
    return render_template('class.html')

@app.route("/class/<classId>", methods=["GET", "PATCH", "DELETE"])
def studentclassid():
    match request.method:
        case 'GET':
            return render_template('classid.html')
        case 'PATCH':
            print("PATCH")
        case 'DELETE':
            print("DELETE")

@app.route("/screen")
def screen():
    return render_template('screen.html', title=screen)

@app.route('/admin')
@auth_required()
def admin():
    return render_template('admin.html')

@app.route('/login')
def show_login():
    session["username"] = request.form.get("username")
    if session.get('logged_in'):
        return redirect(url_for("link"))
    else:
        return render_template('login.html')
      
@app.post("/handle_login")
def handle_login():
    if request.form["password"] == "password" and request.form["username"] == "admin":
        session["logged_in"] = True
    else:
        flash("Invalid Password or Username.", "warning")
        return render_template("login.html")
    return redirect(url_for('link'))

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for("index"))

@app.route("/register")
def register():
    return render_template('register.html', title=register)    

@app.route("/QRgen/<meetingId>", methods = ["GET"])
@auth_required()
def qrgen(meetingId):
    match request.method:
      case 'GET':
       meeting_list = meetingdb.get_meeting(meetingId)
    return render_template("qrgen.html", meetings=meeting_list, meetingId=meetingId, message='dog')

@app.route("/teapot")
def teapot():
    return render_template("teapot.html"), 418

if __name__ == "__main__":
    #ctx = ('zeehond.crt', 'zeehond.key')
    app.run(host=FLASK_IP, port=FLASK_PORT, debug=FLASK_DEBUG)
    #app.run(host=FLASK_IP, port=FLASK_PORT, debug=FLASK_DEBUG, ssl_context=FLASK_RUN_CERT)