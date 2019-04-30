import os
import pymysql
from flask import Flask, render_template, redirect, request, url_for, request, flash, session, g, jsonify
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from config import Config
from forms import LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/images/profile'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

application = Flask(__name__)
app=application
# mail code taken from tutorial and adapted for my use case
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mail = Mail(app)
csrf = CSRFProtect(app)
# Connect to the database.........................

username = os.getenv('C9_USER')
connection = pymysql.connect(host='eu-cdbr-west-02.cleardb.net',
                             user='b53058aa675415',
                             password='c9a3eb67',
                             db='heroku_8771c70ab5190f8',
                            )

#login form........................................................

@app.route('/', methods=['GET','POST'])
def login():
    
 form = LoginForm()
 if g.user:
        return render_template('home.html')
 if request.method == 'POST' and form.validate_on_submit():
     #clears session and gets password and email
       session.pop('user', None)
       password=request.form['password']
       email=request.form['email']
       
       
      # retrieves email and if does not returns to login 
       
       try:
        with connection.cursor() as cursor:
            sql= "SELECT `email` FROM `users` WHERE `email`=%s"
            cursor.execute(sql,(email))
            result = cursor.fetchone()
            
            if result[0] !=email:
                flash('email incorrect')
                return redirect('/')
         #authenticates password using password hash   
            sql= "SELECT `password` FROM `users` WHERE `email`=%s"
            cursor.execute(sql,(email))
            result = cursor.fetchone()
          
            if check_password_hash(result[0], password):
             session['user'] = request.form['email']
             return redirect('home')
                
       except:
             
            flash("incorrect email or password")
          
 return render_template('index.html', form=form)
    
    
#users home screen after signin ...............................................
@app.route('/home')

def home():
    
    if g.user:
        page_title = 'Home'
        email=g.user
        # fetchs profile picture
        try:
            with connection.cursor() as cursor:
                sql= "SELECT `profileImage` FROM `users` WHERE `email`=%s"
                cursor.execute(sql,(g.user))
                session['image'] = cursor.fetchone()
                profilepic=session['image'][0]
                
        except:
             flash('error')
        
        #fetchs user id using session email and then gets badges
        try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
             sql= "SELECT id FROM users WHERE email=%s;"
             cursor.execute(sql,(g.user))
             result = cursor.fetchone()
             userid=result['id']
             
             sql= "SELECT badges.badge,users.name FROM badges INNER JOIN users ON badges.badgegiver=users.id WHERE badgenomId=%s"
             cursor.execute(sql,(userid))
             badges=cursor.fetchall()
            
             if not badges:
                 flash('sorry no badges')
        except: 
            
             flash('error')
        # fetchs feedback to display total on home page
        try:
                 with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                 
                    
                 
                    sql=" SELECT  feedback.feedbacktext, feedback.nominatedId,feedback.nominatorId,feedback.fbdate FROM feedback WHERE nominatedId=%s"
                    cursor.execute(sql,(userid))
                    connection.commit()
                    data=cursor.fetchall()
                    tf=len(data)
                    
         # fetchs profile pics of feedback givers to display home page          
                  
        except:
                    flash('error')
        try:
                 with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql="SELECT users.name, users.profileImage,feedback.nominatorId FROM users INNER JOIN feedback ON feedback.nominatorId=users.id WHERE feedback.nominatedId=%s"
                    cursor.execute(sql,(userid))
                    connection.commit()
                    pi=cursor.fetchall()
                  
        except:
                    connection.close()
                    flash('error')
       
            
        return render_template('home.html', page_title=page_title, profilepic=profilepic, badges=badges, tf=tf, pi=pi)
   
    
    return redirect('/')
# checks session before loading pages   
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

#...Sign up.................................................
    
@app.route('/signup', methods=['GET', 'POST'])

#sign up users to the db
def signup():
#adds page title and form
 page_title = "Sign Up"    
 form = SignUp()
#populate team dropdown
 try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
             sql= "SELECT * FROM teamname;"
             cursor.execute(sql)
             teamname = cursor.fetchall()
          
             
 except: 
     flash('database busy plesae try later')
     return redirect('/') 
         
 if request.method == 'POST' and form.validate_on_submit():
       
       fullname=request.form['fullname']
       team=request.form['teamie'] 
       password=generate_password_hash(request.form['password'])
       email=request.form['email']
       profileImage='blank_profile.png'
       location=4
       #check user e mail does not exsist in db
     
       try:
        with connection.cursor() as cursor:
            sql= "SELECT `email` FROM `users` WHERE `email`=%s"
            cursor.execute(sql,(email))
            result = cursor.fetchall()
            
#checks email is not already in use         
            
            if len(result)!=0:
                flash('already registered')
                return redirect('signup')
# add user to db   
            
            else:
                with connection.cursor() as cursor:
                    sql= "INSERT INTO `users` (`name`, `email`, `password`,`profileImage`,`teamId`,`locationId`) VALUES (%s, %s, %s, %s,%s,%s)"
                    cursor.execute(sql,(fullname,email,password,profileImage,team,location))
                    connection.commit()
                    flash('User created please login')
                    session['user'] = request.form['email']
                    return redirect('/mail')
       except:
        
            flash("An exception occurred")
            
 return render_template('signup.html', form=form, page_title=page_title, teamname=teamname)
 
# send a confirmation e mail when users register...............................................
@app.route("/mail")
def index():
   msg = Message('Hello', sender = 'tidders2000@gmail.com', recipients = [session['user']])
   msg.body = "user sucessfully created for rate my crowd.com"
   mail.send(msg)
   flash('confirmation email sent')
   session.pop('user', None)
   return redirect('/')
   

#logsout user and kills session.......................................................

@app.route("/logout")
def logout():
    session.pop('user', None)
    print('logged out')
    return redirect('/')
    

#allos users to view feedback given by their colleauges...................................
@app.route("/feedback")
def feedback():
    if g.user:
        page_title="My Feedback"
        profilepic=session['image'][0]
        email=session['user']
        try:
        # selects user id from email then fetchs feedback
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
             sql= "SELECT id FROM users WHERE email=%s;"
             cursor.execute(sql,(email))
             result = cursor.fetchone()
             userid=result['id']
             sql= "SELECT feedback.feedbackTitle,feedback.feedbacktext,feedback.fbdate,users.name,users.profileImage FROM feedback INNER JOIN users ON feedback.nominatorId=users.id WHERE nominatedId=%s"
             cursor.execute(sql,(userid))
             feedback=cursor.fetchall()
             
             if not feedback:
                 flash('sorry no feedback')
        except: 
             flash('error')
             connection.close()
        return render_template("feedback.html", page_title=page_title, profilepic=profilepic, feedback=feedback)
    return redirect('/')
    
# allows users to create feedback for their colleauges..........................................    
@app.route("/add_feedback", methods=['POST','GET'])
def add_feedback():
    if g.user:
        page_title="Add Feedback"
        #checks session cookie
        profilepic=session['image'][0]
        # recovers teams for dropdown
        try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
             sql= "SELECT * FROM teamname;"
             cursor.execute(sql)
             teamname = cursor.fetchall()
             
        except: flash('error')
        if request.method=='POST':
             fullname=request.form['fullname']
             email=session['user']
             team=request.form['teamie'] 
             feedback_title=request.form['title']
             feedback_text=request.form['feedbacktext']
             date=datetime.now()
             fbdate=(date.strftime("%Y-%m-%d"))
             flash(fbdate)
             #recover  id for person giving feedback
             try:
                 with connection.cursor() as cursor:
                      sql= "SELECT `id` FROM `users` WHERE `email`=%s"
                      cursor.execute(sql,(email))
                      nominatorId = cursor.fetchone()
                   #recover id for person receving feedback  
                     
                      sql= "SELECT `id` FROM `users` WHERE `name`=%s AND teamId =%s"
                      cursor.execute(sql,(fullname,team))
                      result=cursor.fetchone()
                      nominatedid=result[0]
                   #add feedback   
                      sql="INSERT INTO feedback (nominatorId,feedbackTitle,teamId,feedbacktext,nominatedId,fbdate) VALUES (%s,%s,%s,%s,%s,%s)"
                      cursor.execute(sql,(nominatorId[0],feedback_title,team,feedback_text,nominatedid, fbdate))
                      flash("feedback added")
             except:
                 flash("Sorry data save unsuccessful")
               
        return render_template("add_feedback.html", page_title=page_title, teamname=teamname, profilepic=profilepic)
    return redirect('/')

#allows users to add badges as rewards for colleauges....................................... 
@app.route("/badges", methods=['POST','GET'])
def badges():
    if g.user:
        page_title="Badges"
        profilepic=session['image'][0]
#find teamnames for dropdown
        try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
             sql= "SELECT * FROM teamname;"
             cursor.execute(sql)
             teamname = cursor.fetchall()
             
        except: flash('error')
               
        if request.method=='POST':
             fullname=request.form['fullname']
             team=request.form['teamie'] 
             badge=request.form['badge']
             email=session['user']
#finds users id and id for person nominated for a badge             
             try:
                 with connection.cursor() as cursor:
                      sql= "SELECT `id` FROM `users` WHERE `email`=%s"
                      cursor.execute(sql,(email))
                      badgegiver = cursor.fetchone()
                     
                     
                      sql= "SELECT `id` FROM `users` WHERE `name`=%s AND teamId =%s"
                      cursor.execute(sql,(fullname,team))
                      result=cursor.fetchone()
                      badgenomId=result[0]
                      
                      sql="INSERT INTO badges (badgenomId,badge,badgegiver) VALUES (%s,%s,%s)"
                      cursor.execute(sql,(badgenomId,badge,badgegiver))
                      flash("Badge added")
             except:
                 flash("oopps sorry please try again")
                
             
        
        return render_template("badges.html", page_title=page_title, teamname=teamname, profilepic=profilepic)
    return redirect('/')
    
#allows a user to change their profile information...................................
    
@app.route("/myprofile", methods=['GET', 'POST'])
def myprofile():
    if g.user:
        page_title="My Profile"
        profilepic=session['image'][0]
        email=session['user']
        # retrieve users profile information
        try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql= "SELECT users.name,users.id,users.password,users.biog, users.startdate,users.teamId,users.locationId,teamname.teamname,location.locationname FROM users INNER JOIN teamname ON users.teamId=teamname.id INNER JOIN location ON users.locationId=location.id WHERE `email`=%s"
            cursor.execute(sql,(email))
            result = cursor.fetchall()
            sql= "SELECT * FROM location;"
            cursor.execute(sql)
            location = cursor.fetchall()
            sql= "SELECT * FROM teamname;"
            cursor.execute(sql)
            teamname = cursor.fetchall()
           
        except:
            flash('error')
        #add changed details with if statements to manage blanks and not erase data
        if request.method == 'POST':
                  fullname=request.form['fullname']
                  date=request.form['startdate']
                  biog=request.form['biog']
                  team=request.form['teamie']
                  userid=request.form['id']
                  location=request.form['loca']
                  password=request.form['password']
                  if password!=result[0]['password']:
                   password=generate_password_hash(request.form['password'])  
                  if date=="":
                      date=result[0]['startdate']
               
                  try:
                      with connection.cursor(pymysql.cursors.DictCursor) as cursor: 
                          sql="UPDATE users SET name=%s, password=%s,startdate=%s,biog=%s, teamId=%s, locationId=%s where id=%s"
                          cursor.execute(sql,(fullname,password,date,biog,team,location,userid))
                          connection.commit()
                          flash('data updated')
                          return redirect('myprofile')
                  except:
                        flash('unable to change data')
                     
                  
        return render_template("myprofile.html", page_title=page_title, result=result,teamname=teamname, profilepic=profilepic)
        
            
            
            
    return redirect('/')
    
#help........................................................................................
    
@app.route("/help")
def help():
    if g.user:
        page_title="Help"
        profilepic=session['image'][0]
        return render_template("help.html", page_title=page_title, profilepic=profilepic)  
    return redirect('/')
    
# allowed filenames for profile upload
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS  
           
#allows user to change profile picture this is not my code but lifted of a forum........................................
@app.route('/ppupload', methods=['GET', 'POST'])
def upload_file():
    profilepic=session['image'][0]
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
           
            try:
                 with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql="UPDATE users SET profileImage=%s WHERE email=%s"
                    cursor.execute(sql,(filename,g.user))
                    connection.commit()
                    flash('data added')
                    
                  
            except:
                flash('error loading pic')
               
                
                
                
            return redirect('home')   
    return render_template('ppupload.html', profilepic=profilepic)
# selects names data and converts to json for auto complete form on names...................
@app.route('/names')
#recover users for dropdown list used on forms for user names
def names():
    if g.user:
     try:
                 with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql="SELECT name FROM users"
                    cursor.execute(sql)
                    connection.commit()
                    names=cursor.fetchall()
                    return jsonify(names)
     
     except:
                    flash('error')
                    
    else:
        return('/')
         
 #currently not in use but gets feedback data for reports............................... 
@app.route('/data')
#json data for charts
def data():
    if g.user:
     try:
                 with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql="SELECT * FROM feedback"
                    cursor.execute(sql)
                    connection.commit()
                    data=cursor.fetchall()
                   
                  
     except:
                    flash('error')
                  
     return jsonify(data)
#allows users to view the profiles of all their colleauges..............................
@app.route('/viewprofile')
def view_profile():
  # check session and add title/profile image   
     if g.user:
        page_title="My Colleauges"
        profilepic=session['image'][0]
        try:
         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
          #recover all users from database          
                    sql="SELECT users.id, users.name, users.biog,users.profileImage, teamname.teamname FROM users INNER JOIN teamname ON users.teamId=teamname.id"
                    cursor.execute(sql)
                    result=cursor.fetchall()
                   
                  
        except:
                    flash('error')
                    connection.close()
        return  render_template('viewprofile.html', result=result, profilepic=profilepic, page_title=page_title) 
    
     return redirect('/')
    


  
    
if __name__=='__main__':
    
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
           )
    