import os
from flask import Flask, render_template, redirect, request, url_for, request, flash, session, g
import pymysql
from config import Config
from forms import LoginForm, SignUp
from werkzeug.security import generate_password_hash




app = Flask(__name__)

app.config['SECRET_KEY'] = 'heffalump_34'
username = os.getenv('C9_USER')

# Connect to the database.........................
connection = pymysql.connect(host='localhost',
                             user=username,
                             password='',
                             db='crowd')
#login form................................

@app.route('/', methods=['GET','POST'])
def login():
 form = SignUp()
 if request.method == 'POST' and form.validate_on_submit():
       
       password=generate_password_hash(request.form['password'])
       email=request.form['email']
       
       
       
       try:
        with connection.cursor() as cursor:
            sql= ("SELECT email FROM users WHERE email= {}".format(email))
            cursor.execute(sql)
            result = cursor.fetchone()
            if not result[0]:
                return redirect('/')
            
            sql=("SELECT password FROM users WHERE email = {};".format(email))
            cursor.execute(sql)
            result = cursor.fetchone()
            if result==password:
              session['user'] = request.form['email']
              return redirect(url_for('first_page'))
                
       except:
              # Close the connection, regardless of whether or not the above was successful
            flash("An exception occurred")
          
 return render_template('index.html', form=form)
    
    
#users home screen after signin ...................   
@app.route('/first_page')
def first_page():
    return render_template('first_page.html')
    
@app.route('/signup', methods=['GET', 'POST'])
#sign up users to the db.................................
def signup():
 form = SignUp()
 if request.method == 'POST' and form.validate_on_submit():
       firstname=request.form['firstname']
       lastname=request.form ['lastname']
       password=generate_password_hash(request.form['password'])
       email=request.form['email']
       
       #check user e mail does not esist
       
       try:
        with connection.cursor() as cursor:
            sql= "SELECT `email` FROM `users` WHERE `email`=%s"
            cursor.execute(sql,(email))
            result = cursor.fetchall()
            flash(result)
            
            if len(result)!=0:
                flash('already registered')
                return redirect('signup')
         # add user to db   
            
            else:
                with connection.cursor() as cursor:
                    sql= "INSERT INTO `users` (`firstname`, `lastname`, `email`, `password`) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql,(firstname,lastname,email,password))
                    connection.commit()
                    flash('data added')
                    session['user'] = request.form['email']
                    return redirect(url_for('first_page'))
       except:
              # Close the connection, regardless of whether or not the above was successful
            flash("An exception occurred")
          
 return render_template('signup.html', form=form)
 
@app.route('/ammend_user')
def get_tasks():
    
    try:
    # Run a query 
     with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = " SELECT users.id, users.firstname, users.lastname,location.locationname,teamname.teamname FROM users INNER JOIN location ON location.id=users.id INNER JOIN teamname ON teamname.id=users.teamid"
        cursor.execute(sql)
        result = cursor.fetchall()
        
    except:
    # Close the connection, regardless of whether or not the above was successful
     print("An exception occurred")
    
    
    return render_template("ammend_user.html", users=result)

    
    
if __name__=='__main__':
    
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)
    