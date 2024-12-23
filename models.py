from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash
from datetime import datetime
from flask_migrate import Migrate
from flask_wtf.file import FileField, FileAllowed

db=SQLAlchemy(app)
migrate = Migrate(app, db)

#models

class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),nullable=False,unique=True)
    passhash=db.Column(db.String(64),nullable=False)
    role=db.Column(db.String(16))
    is_flagged=db.Column(db.Boolean,default=False,nullable=False)
    is_admin=db.Column(db.Boolean,default=False,nullable=False)
    profile_pic=db.Column(db.String,nullable=False,default="default_pic.jpg")
    
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
    about=db.Column(db.String,nullable=True)

    adreqs=db.relationship("AdRequest",backref="influencer", lazy=True,cascade='all,delete-orphan')

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
    visibility=db.Column(db.String(16),default="Public")
    spo_id=db.Column(db.Integer,db.ForeignKey("sponsor.id"))
    is_flagged=db.Column(db.Boolean,default=False,nullable=False)
    status=db.Column(db.String(32),default="active") #[active,completed]
    progress=db.Column(db.Integer,nullable=False,default=0)

    adreqs=db.relationship("AdRequest",backref="campaign", lazy=True,cascade='all,delete-orphan')

class AdRequest(db.Model):
    __tablename__="adrequest"
    id=db.Column(db.Integer,primary_key=True)
    influ_id=db.Column(db.Integer,db.ForeignKey("influencer.id"))
    camp_id=db.Column(db.Integer,db.ForeignKey("campaign.id"))
    message=db.Column(db.String(256))
    requirements=db.Column(db.String(256),nullable=False)
    pay_amt=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(32),default="pending") #[pending, accepted, rejected, requested, completed, messaged]

with app.app_context(): #only when flask server/ application is ready then create the tables
    db.create_all()
    admin=User.query.filter_by(is_admin=True).first()
    if not admin:
        admin= User(username='admin',passhash=generate_password_hash('password'),role='Admin',is_admin=True)
        db.session.add(admin)
        db.session.commit()