from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS 
from flask_heroku import Heroku 
from flask_bcrypt import Bcrypt 
from flask_marshmallow import Marshmallow
from flask_mail import Mail, Message

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# mail_settings = {
#     "MAIL_SERVER": "smtp.googlemail.com",
#     "MAIL_PORT": 465,
#     "MAIL_USE_TLS": False,
#     "MAIL_USE_SSL": True,
#     "MAIL_USERNAME": "che.dami@gmail.com",
#     "MAIL_PASSWORD": "madisonfaith"
# }
# app.config.update(mail_settings)

CORS(app)
mail = Mail(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://pdizdhghfvrnrm:175ebc0c8d03d6e6b91d6f732b80746f5303343f3550d65b0a299a4a0a771e56@ec2-174-129-255-4.compute-1.amazonaws.com:5432/dihfrvgg03c37"

heroku = Heroku(app)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Guest Table
class Rsvp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.String(50), nullable=False)
    apt_number = db.Column(db.String(20), nullable=True)
    city_name = db.Column(db.String(20), nullable=False)
    state_name = db.Column(db.String(15), nullable=False)
    postal_code = db.Column(db.String(12), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    partner_name = db.Column(db.String(25), nullable=True)

    def __init__(self, first_name, last_name, street_address, apt_number, city_name, state_name, postal_code, phone_number, email, partner_name):
        self.first_name = first_name
        self.last_name = last_name
        self.street_address = street_address
        self.apt_number = apt_number
        self.city_name = city_name
        self.state_name = state_name
        self.postal_code = postal_code
        self.phone_number = phone_number
        self.email = email
        self.partner_name = partner_name

# Login
class Login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class UserSchema(ma.Schema):
    class Meta: 
        fields = ("id", "username")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Guest
@app.route("/rsvp", methods=["POST"])
def guest_rsvp():
    if request.content_type == "application/json":
        post_data = request.get_json()
        first_name = post_data.get("first_name")
        last_name = post_data.get("last_name")
        street_address = post_data.get("street_address")
        apt_number = post_data.get("apt_number")
        city_name = post_data.get("city_name")
        state_name = post_data.get("state_name")
        postal_code = post_data.get("postal_code")
        phone_number = post_data.get("phone_number")
        email = post_data.get("email")
        partner_name = post_data.get("partner_name")

        record = Rsvp(first_name, last_name, street_address, apt_number, city_name, state_name, postal_code, phone_number, email, partner_name)
        db.session.add(record)
        db.session.commit()

        message = Mail(
        from_email='che.dami@gmail.com',
        to_emails=email,
        subject='RSVP Received',
        html_content="Thank you for RSVP'ing to my event.  I will send an invitation to you as soon as possible to your email: %s" % email)
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(str(e))

        return jsonify("Rsvp Created")
    return jsonify("Error: Request must be sent as JSON")

@app.route("/rsvp/admin/get", methods=["GET"])
def rsvp_admin(): 
    all_rsvps = db.session.query(Rsvp.id, Rsvp.first_name, Rsvp.last_name, Rsvp.street_address, Rsvp.apt_number, Rsvp.city_name, Rsvp.state_name, Rsvp.postal_code, Rsvp.phone_number, Rsvp.email, Rsvp.partner_name).all()
    print(all_rsvps)
    return jsonify(all_rsvps)

@app.route("/rsvp/admin/delete/<id>", methods=['DELETE'])
def rsvp_delete(id):
    record = db.session.query(Rsvp).filter(Rsvp.id == id).first()
    db.session.delete(record)
    db.session.commit()
    return jsonify("Record Deleted")

# Login
@app.route("/auth", methods=["POST"])
def admin_user():
    print("JSON BEING SENT: ",request.get_json(force=True))
    print("CONTENT TYPE: ",request.content_type)
    print("DATA: ",request.data)
    if request.content_type == "application/json":
        post_data = request.get_json()
        username = post_data.get("username")
        password = post_data.get("password")

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        record = Login(username, pw_hash)

        db.session.add(record)
        db.session.commit()

        return jsonify("User Created")
    return jsonify("Error: request must be sent as JSON")

@app.route("/auth/get", methods=["GET"])
def get_admin_user():
    only_admin_user = db.session.query(Login.id, Login.username).first()
    result = users_schema.dump(only_admin_user)
    return jsonify(result)

@app.route("/auth/verify", methods=["POST"])
def verify_user():
    if request.content_type == "application/json":
        post_data = request.get_json()
        username = post_data.get("username")
        password = post_data.get("password")

        hashed_password = db.session.query(Login.password).filter(Login.username == username).first()

        if hashed_password == None:
            return jsonify("Username NOT validated")

        validation = bcrypt.check_password_hash(hashed_password[0], password)

        if validation == True:
            return jsonify("User validated")
        return jsonify("User NOT VALIDATED")
    return jsonify("Error: request must be sent as JSON")

if __name__ == "__main__": 
    app.debug = True
    app.run()