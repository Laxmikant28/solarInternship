from flask import Flask,render_template,request,redirect,jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import re
import pickle
with open("config.json", "r") as c:
    params = json.load(c)["params"]

vector = pickle.load(open('vector.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))
stop_words = pickle.load(open('stop_words.pkl', 'rb'))
categories = ['Billing inquiry','Cancellation request','Product inquiry','Refund request','Technical issue']

customer = Flask(__name__)

if params["local_server"] == "True":
    print("server got....")
    customer.config["SQLALCHEMY_DATABASE_URI"] = params["local_url"]
else:
    customer.config["SQLALCHEMY_DATABASE_URI"] = params["prod_url"]

db = SQLAlchemy(customer)


class customer_inquiry(db.Model):
    ticket_id = db.Column(db.Integer, nullable=False,primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(255))
    customer_description = db.Column(db.String(500))
    ticket_type = db.Column(db.String(11))
    ticket_status = db.Column(db.String(11))

def text_cleaning(text):
    exclude = '!"#$%&\'()*+,-./:;<=>@[\\]^_`{|}~'
    pattern = text.translate(str.maketrans("","",exclude))
    pattern = re.sub('[^a-zA-Z]',' ',pattern)
    pattern = " ".join([word.lower() for word in pattern.split() if word.lower() not in stop_words])
    return pattern

@customer.route('/')
def home():
    return render_template('index.html')

@customer.route('/dashboard',methods = ['GET',"POST"])
def dashboard():
    open = customer_inquiry.query.filter_by(ticket_status='open').all()
    close = customer_inquiry.query.filter_by(ticket_status='close').all()
    pie_data = {'Status Open': len(open), 'Status Close': len(close)}
    Bopen = customer_inquiry.query.filter_by(ticket_type='Billing inquiry', ticket_status='open').all()
    Copen = customer_inquiry.query.filter_by(ticket_type='Cancellation request', ticket_status='open').all()
    Popen = customer_inquiry.query.filter_by(ticket_type='Product inquiry', ticket_status='open').all()
    Ropen = customer_inquiry.query.filter_by(ticket_type='Refund request', ticket_status='open').all()
    Topen = customer_inquiry.query.filter_by(ticket_type='Technical issue', ticket_status='open').all()
    hist_data = {'Billing inquiry':len(Bopen),'Cancellation request':len(Copen),'Product inquiry':len(Popen),'Refund request':len(Ropen),'Technical issue':len(Topen)}


    return render_template(
        'dashboard.html',
        pie_data=pie_data,
        hist_data=hist_data,
    )

@customer.route('/inquiry')
def inquiry():
    return render_template('inquiry.html')

@customer.route('/classify',methods = ['GET',"POST"])
def classify():
    B = customer_inquiry.query.filter_by(ticket_type='Billing inquiry',ticket_status='open').all()
    C = customer_inquiry.query.filter_by(ticket_type='Cancellation request',ticket_status='open').all()
    P = customer_inquiry.query.filter_by(ticket_type='Product inquiry',ticket_status='open').all()
    R = customer_inquiry.query.filter_by(ticket_type='Refund request',ticket_status='open').all()
    T = customer_inquiry.query.filter_by(ticket_type='Technical issue',ticket_status='open').all()

    return render_template('classify.html',lenB=len(B),lenC=len(C),lenP=len(P),lenR=len(R),lenT=len(T),comments=[], category=None)

@customer.route('/category/<category_name>')
def category(category_name):
    B = customer_inquiry.query.filter_by(ticket_type='Billing inquiry', ticket_status='open').all()
    C = customer_inquiry.query.filter_by(ticket_type='Cancellation request', ticket_status='open').all()
    P = customer_inquiry.query.filter_by(ticket_type='Product inquiry', ticket_status='open').all()
    R = customer_inquiry.query.filter_by(ticket_type='Refund request', ticket_status='open').all()
    T = customer_inquiry.query.filter_by(ticket_type='Technical issue', ticket_status='open').all()
    comments = customer_inquiry.query.filter_by(ticket_type=category_name,ticket_status='open').all()
    return render_template('classify.html', comments=comments, category=category_name,lenB=len(B),lenC=len(C),lenP=len(P),lenR=len(R),lenT=len(T))

@customer.route('/submit',methods = ["POST"])
def submit():
    customer_name = request.form["name"]
    customer_email = request.form["email"]
    customer_description = request.form["description"]
    sent = text_cleaning(customer_description)
    pred = model.predict(vector.transform([sent]))
    category = categories[pred[0]]
    new_row = customer_inquiry(customer_name=customer_name, customer_email=customer_email, customer_description=customer_description,
                               ticket_type = category , ticket_status = 'open')
    db.session.add(new_row)
    db.session.commit()
    return render_template('inquiry.html')

if __name__ == "__main__":
    customer.run(debug=True)