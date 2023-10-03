from flask import Flask,flash,redirect,request,url_for,render_template,session,send_file
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from mail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
app=Flask(__name__)
app.secret_key='bhargavi#2002'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='results'
Session(app)
mysql=MySQL(app)
@app.route('/',methods=['GET','POST'])
def home():
    if request.method=="POST":
        print(request.form) 
        name=request.form['name'] 
        emailid=request.form['email'] 
        message=request.form['message'] 
        cursor=mysql.connection.cursor()
        cursor.execute('insert into contactus(name,email,text) values(%s,%s,%s)',[name,emailid,message]) 
        mysql.connection.commit()
        flash('contactus details submitted')
        return render_template('home.html')
    return render_template('home.html')
@app.route('/registration',methods=['GET','POST'])
def register():
    cursor=mysql.connection.cursor()
    cursor.execute('select count(*) from admin')
    count=cursor.fetchone()[0]
    cursor.close()
    if (count>=0):
        return 'admin already registered'
    if request.method=='POST':
        name=request.form['name']
        password=request.form['password']
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from admin')
        data=cursor.fetchall()
        cursor.execute('SELECT email from admin')
        edata=cursor.fetchall()
        if (email,) in edata:
            flash('Email id already exists')
            return render_template('register.html')
        cursor.close()
        otp=genotp()
        sendmail(email,otp)
        return render_template('otp.html',otp=otp,name=name,password=password,email=email)
    else:
        return render_template('register.html')
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    if request.method=='POST':
        name=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from  admin where name=%s and password=%s',[name,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid username or password')
            return render_template('login.html')
        else:
            session['user']=name
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
    return render_template('dashboard.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
    return render_template('login.html')
@app.route('/otp/<otp>/<name>/<password>/<email>',methods=['GET','POST'])
def otp(otp,name,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            lst=[name,password,email]
            query=f'insert into admin values(%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,name=name,password=password,email=email)
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        uname=request.form['username']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from admin')
        data=cursor.fetchall()
        if (uname,) in data:
            cursor.execute('select email from admin where name=%s',[uname])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using {request.host+url_for("createpassword",token=token(uname,360))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user name'
    return render_template('forgot.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        uname=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where name=%s',[npass,uname])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'
@app.route('/addstudents',methods=['GET','POST'])
def addstudents():
    if session.get('user'):
        if request.method=='POST':
           stdid=request.form['id1']
           stdname=request.form['name']
           section=request.form['section']
           mobile=request.form['mblnumber']
           address=request.form['address']
           dept=request.form['dept']
           cursor=mysql.connection.cursor()
           cursor.execute('insert into addstudents(stdid,stdname,section,mobile,address,dept)values(%s,%s,%s,%s,%s,%s)',[stdid,stdname,section,mobile,address,dept])
           mysql.connection.commit()
           cursor.close()
           flash('Details Registered')
           return redirect(url_for('dashboard'))
        return render_template('addstudent.html')
    else:
        
        return redirect(url_for('login'))
@app.route('/addsubjects',methods=['GET','POST'])
def addsubjects():
    if session.get('user'):
        if request.method=='POST':
           cid=request.form['number']
           ctitle=request.form['name']
           maxmarks=request.form['marks']
           cursor=mysql.connection.cursor()
           cursor.execute('insert into addsubjects(courseid,coursetitle,maxmarks)values(%s,%s,%s)',[cid,ctitle,maxmarks])
           mysql.connection.commit()
           cursor.close()
           flash('Details Registered')
           return redirect(url_for('dashboard'))
        return render_template('addsubject.html')
    else:
        return redirect(url_for('login'))
@app.route('/studentrecord')
def studentrecord():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from addstudents')
        students_data=cursor.fetchall()
        print(students_data)
        cursor.close()
        return render_template('studentrecord.html',data=students_data)
    else:
        return redirect(url_for('login'))
@app.route('/updaterecords/<stdid>',methods=['GET','POST'])
def updaterecords(stdid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select stdid,stdname,section,mobile,address,dept from addstudents where stdid=%s',[stdid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
           stdid=request.form['id1']
           stdname=request.form['name']
           section=request.form['section']
           mobile=request.form['mblnumber']
           address=request.form['address']
           dept=request.form['dept']
           cursor=mysql.connection.cursor()
           cursor.execute('update addstudents set stdname=%s,section=%s,mobile=%s,address=%s,dept=%s where stdid=%s',[stdname,section,mobile,address,dept,stdid])
           mysql.connection.commit()
           cursor.close()
           flash('Records updated successfully')
           return redirect(url_for('studentrecord'))
        return render_template('updaterecord.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/deleterecords/<stdid>')
def deleterecords(stdid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from addstudents where stdid=%s',[stdid])
    mysql.connection.commit()
    cursor.close()
    flash('Records deleted successfully')
    return redirect(url_for('studentrecord'))
@app.route('/subjectrecord')
def subjectrecord():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from addsubjects')
        subjects_data=cursor.fetchall()
        print(subjects_data)
        cursor.close()
        return render_template('subjectrecord.html',data=subjects_data)
    else:
        return redirect(url_for('login'))
@app.route('/update/<courseid>',methods=['GET','POST'])
def update(courseid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select courseid,coursetitle,maxmarks from addsubjects where courseid=%s',[courseid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
           courseid=request.form['number']
           coursetitle=request.form['name']
           maxmarks=request.form['marks']
           cursor=mysql.connection.cursor()
           cursor.execute('update addsubjects set coursetitle=%s,maxmarks=%s where courseid=%s',[coursetitle,maxmarks,courseid])
           mysql.connection.commit()
           cursor.close()
           flash('Records updated successfully')
           return redirect(url_for('subjectrecord'))
        return render_template('update.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/delete/<courseid>')
def delete(courseid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from addsubjects where courseid=%s',[courseid])
    mysql.connection.commit()
    cursor.close()
    flash('Records deleted successfully')
    return redirect(url_for('subjectrecord'))
@app.route('/addsemresult',methods=['GET','POST'])
def addsemresult():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT stdid from addstudents')
        data=cursor.fetchall()
        cursor.execute('select courseid from addsubjects')
        cdata=cursor.fetchall()
        if request.method=='POST':
            id1=request.form['id']
            course=request.form['course']
            section=request.form['section']
            semt=request.form['sem']
            smarks=request.form['marks']
            cursor=mysql.connection.cursor()
            cursor.execute('insert into semresults(stdid,courseid,section,sem,semmarks) values(%s,%s,%s,%s,%s)',(id1,course,section,semt,smarks))
            cursor.connection.commit()
            cursor.close()
            flash(f'added successfully')
            return redirect(url_for('dashboard'))
        return render_template('addsemresults.html',data=data,cdata=cdata)
    else:
        return redirect(url_for('login'))
@app.route('/addinternalresult',methods=['GET','POST'])
def addinternalresult():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT stdid from addstudents')
        data=cursor.fetchall()
        cursor.execute('SELECT COURSEID FROM addsubjects')
        cdata=cursor.fetchall()
        if request.method=='POST':
            id1=request.form['id']
            course=request.form['course']
            section=request.form['section']
            int1=request.form['internalI']
            imarks1=request.form['marks']
            int2=request.form['internalII']
            imarks2=request.form['marks']
            cursor=mysql.connection.cursor()
            cursor.execute('insert into internalresults value(%s,%s,%s,%s,%s,%s,%s)',(id1,course,section,int1,imarks1,int2,imarks2))
            cursor.connection.commit()
            flash(f'added successfully')
            return redirect(url_for('dashboard'))
        return render_template('addinternalresults.html',data=data,cdata=cdata)
    else:
        return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        if request.method=='POST':
            search=request.form['search']
            cursor=mysql.connection.cursor()
            cursor.execute('select a.stdid,a.courseid,a.sem,a.semmarks,i.Internal1,i.internalmarks1,i.Internal2,i.internalmarks2 from addstudents as s inner join semresults as a on s.stdid=a.stdid inner join internalresults as i on s.stdid=i.stdid and i.courseid=a.courseid where s.stdid=%s',[search])
            data=cursor.fetchall()
            mysql.connection.commit()
            cursor.close()
            if not data:
                flash(f'invaild rollno')
            return render_template('search.html',data=data)
        return render_template('search.html')
@app.route('/editsemresult',methods=['GET','POST'])
def editsemresult():
    if session.get('user'):
        if request.method=='POST':
            search=request.form['search']
            cursor=mysql.connection.cursor()
            cursor.execute('select a.stdid,a.courseid,a.sem,a.semmarks,i.Internal1,i.internalmarks1,i.Internal2,i.internalmarks2 from addstudents as s inner join semresults as a on s.stdid=a.stdid inner join internalresults as i on s.stdid=i.stdid and i.courseid=a.courseid where s.stdid=%s',[search])
            data=cursor.fetchall()
            mysql.connection.commit()
            cursor.close()
            return render_template('semresults.html',data=data)
        return render_template('semresults.html')
    
@app.route('/semdelete/<stdid>/<courseid>')
def semdelete(stdid,courseid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from semresults where stdid=%s and courseid=%s',[stdid,courseid])
    cursor.execute('delete from internalresults where stdid=%s and courseid=%s',[stdid,courseid])
    mysql.connection.commit()
    cursor.close()
    flash('Records deleted successfully')
    return render_template('semresults.html')
@app.route('/internalresults',methods=['GET','POST'])
def internalresults():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select i.stdid,i.courseid,i.Internal1,i.internalmarks1,i.Internal2,i.internalmarks2 from addstudents as s inner join internalresults as i on s.stdid=i.stdid')
        data=cursor.fetchall()
        if request.method=='POST':
            search=request.form['search']
            cursor=mysql.connection.cursor()
            cursor.execute('select a.stdid,a.courseid,a.sem,a.semmarks,i.Internal1,i.internalmarks1,i.Internal2,i.internalmarks2 from addstudents as s inner join semresults as a on s.stdid=a.stdid inner join internalresults as i on s.stdid=i.stdid and i.courseid=a.courseid where s.stdid=%s',[search])
            data=cursor.fetchall()
            mysql.connection.commit()
            cursor.close()
            return render_template('internalresults.html',data=data)
        return render_template('internalresults.html',data=data)
@app.route('/deleted/<stdid>/<courseid>')
def deleted(stdid,courseid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from internalresults where stdid=%s and  courseid=%s',[stdid,courseid])
    mysql.connection.commit()
    cursor.close()
    flash('Records deleted successfully')
    return render_template('internalresults.html')
      


        

app.run(debug=True,use_reloader=True)
