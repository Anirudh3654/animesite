from flask import Flask,request,render_template,request, redirect, url_for,flash,send_file
from werkzeug.utils import secure_filename
import urllib.request
import base64
from PIL import Image
import io
import os
import boto3,botocore
import pymysql
import datetime

conn= pymysql.connect(host = 'tested.cya2lw5rkrbc.ap-south-1.rds.amazonaws.com' , port = 3306 ,user = 'Anirudh' , password = 'Ani##365##' ,db = 'anime' )

app=Flask(__name__)
app.secret_key = "secret-key"
app.config['UPLOAD_FOLDER']='static/upload'
app.config['MAX_COUNT_LENGTH']= 16 * 1024 *1024
ALLOWED_EXTENSIONS=set(['img','jpg','jpeg','gif'])
app.config['S3_BUCKET'] = "storeimages365"
app.config['S3_KEY'] = "AKIAWLPJMG63EBZEIGCG"
app.config['S3_SECRET'] = "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"
app.config['S3_LOCATION'] = 'http://{}.s3.ap-south-1.amazonaws.com/'.format(app.config['S3_BUCKET'])

s3 = boto3.client(
   "s3",
   aws_access_key_id=app.config['S3_KEY'],
   aws_secret_access_key=app.config['S3_SECRET']
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
    
    
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('login.html')


@app.route('/login', methods =['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        admin=request.form.getlist('isadmin')
        #for admin login
        curr=conn.cursor()
        curr.execute('SELECT * FROM anime.admin')
        admin_details=curr.fetchall()
        if 'Yes' in admin:
            for i in admin_details:
                if i[0]==username and i[1]==password:
                    return render_template('AddAnime.html',show_results=1)
        #for normal login
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM anime.newlogin where username=(%s)",(username))
        details=cursor.fetchall()
        #getting login time
        time=str(datetime.datetime.now())
        ip=str(request.remote_addr)
        cursor.execute('INSERT INTO anime.logininfo (username,time_loggin,ip) values(%s,%s,%s)',(username,time,ip))
        conn.commit()
        image=details[0][2]
        for i in details:
            if i[0]==username and i[1]==password:
                return render_template('AddAnime.html',image=image,username=username)
    return render_template('login.html')


@app.route('/find',methods=['GET','POST'])
def find():
    if request.method=='POST' and 'username' in request.form:
        username=request.form['username']
        cur=conn.cursor()
        cur.execute("SELECT * FROM anime.logininfo where username=(%s)",(username))
        details=cur.fetchall()
        x=list(details)
        return render_template('disptime.html',data=x)
    return render_template('adminpage.html')
    
    
@app.route('/register', methods =['GET', 'POST'])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        file = request.files['file']
        file.filename= secure_filename(file.filename)
        output = str(send_to_s3(file, app.config["S3_BUCKET"]))

        if username not in get_details_login():
            insert_user(username,password,output)
            return render_template('login.html')
    return render_template('register.html')



def send_to_s3(file, bucket_name, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return "{}{}".format(app.config["S3_LOCATION"],file.filename)
    
def convertToBinaryData(filename):
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData
    
def insert_details(ranking,name,genere):
    cur=conn.cursor()
    cur.execute("INSERT INTO anime.ranking (ranking,name,genere) VALUES (%s,%s,%s)", (ranking,name,genere))
    conn.commit()
    
def insert_user(username,password,file):
    cur=conn.cursor()
    cur.execute("INSERT INTO anime.newlogin (username,password,file) VALUES (%s,%s,%s)",(username,password,file))
    conn.commit()
    
def delete_details(name):
    cur=conn.cursor()
    cur.execute("DELETE FROM anime.ranking where name=(%s)",(name))
    conn.commit()

def get_details_login():
    cur=conn.cursor()
    cur.execute("SELECT *  FROM anime.newlogin")
    details = cur.fetchall()
    a=list()
    for i in details:
        a.append(i[0])
    return a
    
def get_details():
    cur=conn.cursor()
    cur.execute("SELECT *  FROM anime.ranking")
    details = cur.fetchall()
    a=list()
    for i in details:
        a.append(i[0])
    return a


@app.route('/delete',methods = ['post'])
def delete():
    if request.method == 'POST':
        name=request.form['name']
        delete_details(name)
        return showenteries()
        
@app.route('/insert',methods = ['post'])
def insert():
    if request.method == 'POST':
        ranking = request.form['ranking']
        name = request.form['name']
        genere = request.form['genere']
        eg=get_details()
        if ranking not in eg:
            insert_details(ranking,name,genere)
            return showenteries()
        else:
            return "Please go back and input a unique entry"
        
@app.route('/entries')
def showenteries():
    cur=conn.cursor()
    cur.execute("SELECT * FROM anime.ranking")
    details=cur.fetchall()
    return render_template('display.html',data=details)
    
@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)
if  __name__=="__main__":
	app.run(debug=True)
