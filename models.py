from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash
from datetime import datetime

db=SQLAlchemy(app)

#models

class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),nullable=False,unique=True)
    passhash=db.Column(db.String(64),nullable=False)
    role=db.Column(db.String(16),default="User")
    is_flagged=db.Column(db.Boolean,default=False,nullable=False)
    is_admin=db.Column(db.Boolean,default=False,nullable=False)

    sponsors=db.relationship('Sponsor',backref="user",lazy=True,cascade='all,delete-orphan')
    influencers=db.relationship('Influencer',backref="user",lazy=True,cascade='all,delete-orphan')
    

class Sponsor(db.Model):
    __tablename__="sponsor"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(32),nullable=False,unique=True)
    industry=db.Column(db.String(64))
    budget=db.Column(db.Integer,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"))

    campaigns=db.relationship('Campaign',backref="sponsor")
    


class Influencer(db.Model):
    __tablename__="influencer"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,unique=True,nullable=False)
    reach=db.Column(db.String(16))
    niche=db.Column(db.String(256))
    category=db.Column(db.String(256),nullable=False)
    platform=db.Column(db.String(64))
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    profile_pic=db.Column(db.String,nullable=False,default="default_pic.jpg")
    about=db.Column(db.String,nullable=True)

    adreqs=db.relationship("AdRequest",backref="influencer", lazy=True,cascade='all,delete-orphan')
    messages=db.relationship("Message",backref="influencer", lazy=True, cascade="all,delete-orphan")

class Campaign(db.Model):
    __tablename__="campaign"
    id=db.Column(db.Integer,primary_key=True)
    camp_name=db.Column(db.String(32),nullable=False,unique=True)
    description=db.Column(db.String(256))
    niche=db.Column(db.String(256))
    budget=db.Column(db.Integer,nullable=False)
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date,nullable=False)
    goals=db.Column(db.String(256))
    visibility=db.Column(db.String(16),default="public")
    spo_id=db.Column(db.Integer,db.ForeignKey("sponsor.id"))
    is_flagged=db.Column(db.Boolean,default=False,nullable=False)
    status=db.Column(db.String(32),default="active") #[active,completed,progress(?)]

    adreqs=db.relationship("AdRequest",backref="campaign", lazy=True,cascade='all,delete-orphan')

class AdRequest(db.Model):
    __tablename__="adrequest"
    id=db.Column(db.Integer,primary_key=True)
    influ_id=db.Column(db.Integer,db.ForeignKey("influencer.id"))
    camp_id=db.Column(db.Integer,db.ForeignKey("campaign.id"))
    #messages=db.Column(db.String(256))
    requirements=db.Column(db.String(256),default="to be written by sponsor")
    pay_amt=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(32),default="pending") #[pending, accepted, rejected, requested, completed, messaged]

    messages=db.relationship("Message",backref="adrequest", lazy=True, cascade="all,delete-orphan")


class Message(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    message_body=db.Column(db.String(256),nullable=False)
    ad_id=db.Column(db.Integer,db.ForeignKey("adrequest.id"))
    influ_id=db.Column(db.Integer,db.ForeignKey("influencer.id"))
    datetime=db.Column(db.DateTime,nullable=False,default=datetime.now())

class Rating(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    camp_id=db.Column(db.Integer,db.ForeignKey("campaign.id"))
    influ_id=db.Column(db.Integer,db.ForeignKey("influencer.id"))
    rating=db.Column(db.Integer)


with app.app_context(): #only when flask server/ application is ready then create the tables
    db.create_all()
    admin=User.query.filter_by(is_admin=True).first()
    if not admin:
        admin= User(username='admin',passhash=generate_password_hash('password'),role='Admin',is_admin=True)
        db.session.add(admin)
        db.session.commit()