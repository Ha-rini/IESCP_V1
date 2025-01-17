from flask import Flask,render_template,request, redirect, session, url_for,flash
from models import db, User, Sponsor, Influencer, AdRequest, Campaign
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from collections import Counter, defaultdict
from sqlalchemy import or_,and_
from imghdr import what
import os

from werkzeug.utils import secure_filename

from app import app


def check_session(func):
    @wraps(func) #to avoid the server throwing an error for not having unique functions;   func-placeholder for the function passed (eg. profile(), login(), etc.)
    def wrapper(*args, **kwargs): #pack and unpacking of : args- positional arguments ; kwargs- keyword arguments
        if 'username' not in session:
            flash("You need to login first!",category="danger")
            return redirect(url_for('login'))
        user=User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('logout'))
        return func(*args, **kwargs)
    return wrapper

def check_admin(func):
    @wraps(func) #to avoid the server throwing an error for not having unique functions;   func-placeholder for the function passed (eg. profile(), login(), etc.)
    def wrapper(*args, **kwargs): #pack and unpacking of : args- positional arguments ; kwargs- keyword arguments
        if 'username' not in session:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        user=User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        if not user.is_admin:
            flash("You are not authorized to visit this page",category="danger")
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return wrapper


@app.route('/',methods=['GET','POST'])
def re():
    return redirect('/login')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form.get('log_email')
        password=request.form.get('password')
        user=User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.passhash,password):
            flash("Incorrect credentials",category="danger")
            return redirect(url_for('login'))
        if user.is_flagged==True:
            flash("You have been flagged and cannot login. Please contact the admin for further details",category="danger")
            return redirect(url_for('login'))
        session['username']=username
        return redirect(url_for('home'))
    return render_template("login.html")

@app.route('/register',methods=['GET','POST'])
def register():
    
    if request.method=="POST":
        username=request.form.get('reg_email')
        password=request.form.get('password')
        confirm=request.form.get('confirm')
        role=request.form.get('role')        
        if not username or not password or not confirm or not role:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('register'))
        if not password==confirm:
            flash("confirm password and password are not same",category="danger")
            return redirect(url_for('register'))
        user=User.query.filter_by(username=username).first()
        if user:
            flash("Please choose another username",category="danger")
            return redirect(url_for('register'))
        user =User(role=role, username=username, passhash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        if user.role=="Sponsor":
            return redirect(url_for('spo_register',user_id=user.id))
        if user.role=="Influencer":
            return redirect(url_for('influ_register',user_id=user.id))
    return render_template("register.html")

@app.route('/sponsor_register',methods=['GET','POST'])
def spo_register():
    user_id=request.args.get('user_id')
    print(user_id)
    user=User.query.filter_by(id=user_id).first()
    print(user)
    if not user:
        flash("You have to register yourself first", category="danger")
        return redirect(url_for('register'))
    if request.method=="POST":
        name=request.form.get('spo-name')
        industry=request.form.get('industry')
        budget=request.form.get('budget')
        print(name,user.id)
        sponsor=Sponsor.query.filter_by(name=name).first()
        if sponsor:
            flash('The name aldready exists',category="danger")
            return redirect(url_for('spo_register',user_id=user.id))
        if not name or not budget:
            flash("Please fill all the fields",category="danger")
            return redirect(url_for('spo_register'))
        if len(name) > 32:
            flash("Name should not be longer 32 characters ",category="danger")
            return redirect(url_for('spo_register'))
        if industry and len(industry) > 64:
            flash("Name should not be longer 32 characters ",category="danger")
            return redirect(url_for('spo_register'))
        sponsor=Sponsor(name=name, industry=industry, budget=budget,user=user)
        db.session.add(sponsor)
        db.session.commit()
        
        flash("Registration successful. Please login to continue",category="success")
        return redirect(url_for('login'))

    return render_template('Sponsor/spo_register.html',user=user)

@app.route('/influencer_register',methods=['GET','POST'])
def influ_register():
    user_id=request.args.get('user_id')
    print(user_id)
    user=User.query.filter_by(id=user_id).first()
    print(user)
    if not user:
        flash("You have to register yourself first", category="danger")
        return redirect(url_for('register'))
    if request.method=="POST":
        name=request.form.get('name')
        niche=request.form.get('niche')
        reach=request.form.get('reach')
        category=request.form.get('category')
        platform=request.form.get('platform')
        print(name,user.id)
        
        if not name or not category or not platform:
            flash("Please fill all the fields",category="danger")
            return redirect(url_for('influ_register'))
        if len(name) > 32:
            flash("Name should not be longer 32 characters ",category="danger")
            return redirect(url_for('influ_register'))
        if niche and len(niche) > 256:
            flash("Niche should not be longer 256 characters ",category="danger")
            return redirect(url_for('influ_register'))
        if not niche:
            niche=None
        if len(platform) > 64:
            flash("Platfrom should not be longer 64 characters ",category="danger")
            return redirect(url_for('influ_register'))
        
        influencer=Influencer(name=name, niche=niche, category=category, reach=reach, platform=platform ,user=user)
        db.session.add(influencer)
        db.session.commit()
        
        flash("Registration successful. Please login to continue",category="success")
        return redirect(url_for('login'))

    return render_template('Influencer/influ_register.html',user=user)


@app.route('/home',methods=['GET','POST'])
@check_session # home=check_session(home)
def home():
    username=session['username']
    user=User.query.filter_by(username=username).first()
 
    if user.role=="Sponsor":
        sponsor=Sponsor.query.filter_by(user_id=user.id).first()
        if not sponsor:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        return render_template("Sponsor/spondash.html",sponsor=sponsor)
    elif user.role=="Influencer":
        influencer=Influencer.query.filter_by(user_id=user.id).first()
        if not influencer:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        pending_adreqs = AdRequest.query.join(Campaign, AdRequest.camp_id == Campaign.id).filter(
                            AdRequest.influ_id == influencer.id,
                            AdRequest.status == "pending",
                            Campaign.is_flagged == False
                        ).all()
        accepted_adreqs = AdRequest.query.join(Campaign, AdRequest.camp_id == Campaign.id).filter(
                            AdRequest.influ_id == influencer.id,
                            AdRequest.status == "accepted",
                            Campaign.is_flagged == False
                        ).all()
        requested_adreqs = AdRequest.query.join(Campaign, AdRequest.camp_id == Campaign.id).filter(
                            AdRequest.influ_id == influencer.id,
                            AdRequest.status == "requested",
                            Campaign.is_flagged == False
                        ).all()
        completed_adreqs = AdRequest.query.join(Campaign, AdRequest.camp_id == Campaign.id).filter(
                            AdRequest.influ_id == influencer.id,
                            AdRequest.status == "completed",
                            Campaign.is_flagged == False
                        ).all()
        print(accepted_adreqs)
        return render_template("Influencer/infludash.html",influencer=influencer,pending_adreqs=pending_adreqs,
                               accepted_adreqs=accepted_adreqs,requested_adreqs=requested_adreqs,
                               completed_adreqs=completed_adreqs)
    elif user.role=="Admin":
        if not user.is_admin:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        users=User.query.all()
        campaigns=Campaign.query.all()
        adreqs=AdRequest.query.all()
        return render_template("Admin/admindash.html",users=users,campaigns=campaigns,adreqs=adreqs)
    else:
        return render_template("home.html",user=user)

@app.route('/search')
@check_session
def search():
    username=session['username']
    user=User.query.filter_by(username=username).first()
    if user.role=='Sponsor':
        return redirect(url_for('sponsor_search'))
    if user.role=='Influencer':
        return redirect(url_for('search_campaign'))
    if user.role=='Admin':
        return redirect(url_for('admin_search'))

@app.route('/searchcampaigns')
@check_session
def search_campaign():
    query=request.args.get('search')
    campaigns=None
    all_campaigns=Campaign.query.filter_by(is_flagged=0,visibility="Public").all()
    if query:
        campaigns = Campaign.query.filter(
            Campaign.camp_name.ilike(f'%{query}%'),
            Campaign.is_flagged == False,
            Campaign.visibility == "Public"
        ).all()
        campaigns.extend(Campaign.query.filter(
            Campaign.niche.ilike(f'%{query}%'),
            Campaign.is_flagged == False,
            Campaign.visibility == "Public"
        ).all())
        campaigns=list(set(campaigns))
        print(campaigns)
    return render_template('Influencer/search.html',query=query,all_campaigns=all_campaigns, campaigns=campaigns)

@app.route('/sponsorsearch')
@check_session
def sponsor_search():
    username=session['username']
    user=User.query.filter_by(username=username).first()
    query=request.args.get('search')
    campaigns=None
    all_campaigns=(Campaign.query.join(Campaign.sponsor).
                    join(Sponsor.user).
                    filter(Campaign.is_flagged==0,User.id==user.id)).all()
    print(all_campaigns)
    influencers=None
    all_influencers = Influencer.query.join(Influencer.user).filter(User.is_flagged == False).all()
    if query:
        campaigns = (Campaign.query.join(Campaign.sponsor).
                    join(Sponsor.user).
                    filter(Campaign.camp_name.ilike(f'%{query}%'),
                           Campaign.is_flagged==0,User.id==user.id)).all()
        campaigns.extend(Campaign.query.join(Campaign.sponsor).
                    join(Sponsor.user).filter(
                        Campaign.niche.ilike(f'%{query}%'),
                        Campaign.is_flagged==0,
                        User.id==user.id).all())
        influencers=Influencer.query.join(Influencer.user).filter(
                        Influencer.name.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.niche.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.reach.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.category.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        campaigns=list(set(campaigns))
        influencers=list(set(influencers))
    return render_template('Sponsor/search.html',query=query,all_campaigns=all_campaigns, campaigns=campaigns,all_influencers=all_influencers,influencers=influencers)


@app.route('/adminsearch')
@check_session
def admin_search():
    query=request.args.get('search')
    campaigns=None
    users=None
    all_users=User.query.all()
    all_campaigns=Campaign.query.all()
    if query:
        campaigns=Campaign.query.filter(Campaign.camp_name.ilike(f'%{query}%')).all()
        campaigns.extend(Campaign.query.filter(
            Campaign.niche.ilike(f'%{query}%')
        ).all())
        users=User.query.filter(User.username.ilike(f'%{query}%')).all()
        print(users, campaigns)
        campaigns=list(set(campaigns))
    return render_template('Admin/search.html',query=query,all_users=all_users,all_campaigns=all_campaigns,users=users,campaigns=campaigns)

@app.route('/searchinfluencer/<int:id>')
@check_session
def search_influencer(id):
    query=request.args.get('search')
    influencers=None
    source = request.args.get('source', 'add')  # Default to 'add' if not provided
    ad_id = request.args.get('ad_id') if source == 'edit' else None

    print(source)
    all_influencers = Influencer.query.join(Influencer.user).filter(
                    User.is_flagged == False).all()
    if query:
        influencers=Influencer.query.join(Influencer.user).filter(
                        Influencer.name.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.niche.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.reach.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        influencers.extend(Influencer.query.join(Influencer.user).filter(
                        Influencer.category.ilike(f'%{query}%'),
                        User.is_flagged==False
                    ).all()
                    )
        influencers=list(set(influencers))
        print(influencers)
    return render_template('Sponsor/search_influencer.html',query=query,all_influencers=all_influencers,
                           influencers=influencers,id=id,source=source,ad_id=ad_id)

@app.route('/viewprofile/<int:id>/<int:influ_id>')
@check_session
def view_profile(id,influ_id):
    campaign=Campaign.query.get(id)
    influencer=Influencer.query.get(influ_id)
    source = request.args.get('source', 'add')  # Default to 'add' if not provided
    ad_id = request.args.get('ad_id') if source == 'edit' else None

    if not influencer:
        flash("Influencer you are looking for doesn't exist",category="danger")
        return redirect(url_for('sponsor_search'))
    user=User.query.filter_by(id=influencer.user_id).first()
    profile_pic=url_for('static',filename='profile_pics/' + user.profile_pic)
    adreqs=(AdRequest.query
                .join(Influencer, AdRequest.influ_id == Influencer.id)
                .join(Campaign, AdRequest.camp_id == Campaign.id)
                .filter(AdRequest.status.in_(["completed", "accepted"]),Influencer.id==influencer.id)
                .all())
    print(source)
    return render_template("Sponsor/viewprofile.html",influencer=influencer,
                           campaign=campaign,adreqs=adreqs,profile_pic=profile_pic,
                           source=source,ad_id=ad_id)


@app.route('/selectinfluencer/<int:id>/<int:influ_id>')
@check_session
def select_influencer(id,influ_id):
    influencer=Influencer.query.get(influ_id)
    campaign=Campaign.query.get(id)
    source = request.args.get('source','add')  # Default to 'add' if not provided
    print(source)
    ad_id = request.args.get('ad_id') if source == 'edit' else None
    if source == 'edit':
        adreq=AdRequest.query.get(ad_id)
        print(adreq)
        print(influencer)
        return render_template('Sponsor/AdRequests/edit.html', campaign=campaign, adreq=adreq, influencer=influencer,source=source)
    else:
        return render_template('Sponsor/AdRequests/add.html', campaign=campaign, influencer=influencer,source=source)


@app.route('/influencer/adrequest/request/<int:id>',methods=['GET','POST'])
@check_session
def request_adreq(id):
    campaign=Campaign.query.get(id)
    username=session['username']
    user=User.query.filter_by(username=username).first()
    influencer=Influencer.query.filter_by(user_id=user.id).first()
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    if request.method=='POST':
        influname=request.form.get("influ-name")
        campname=request.form.get("camp-name")
        message=request.form.get("message")
        requirements=request.form.get("requirements")
        pay_amt=request.form.get("amt")
        print(message)
        campaign=Campaign.query.filter_by(camp_name=campname).first()
        print(influname,campname,message,requirements,pay_amt)
        if not influname or not campname or not message or not pay_amt or not requirements:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('request_adreq',id=id))
        if not influencer:
            flash("Influencer name doesn't exist. Check the spelling or find an influencer",category="danger")
            return redirect(url_for('request_adreq',id=id))
        if not campaign:
            flash("Camapign doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq=AdRequest.query.filter_by(influ_id=influencer.id,camp_id=campaign.id).first()
        if adreq:
            flash("You have already received the ad request or sent an ad request or rejected the ad request",category="danger")
            return redirect(url_for('home'))    
        status='requested'    
        adreq=AdRequest(requirements=requirements, pay_amt=pay_amt, influencer=influencer, campaign=campaign,status=status,message=message)
        db.session.add(adreq)
        db.session.commit()
        flash("Ad Request sent successfully",category="success")
        return redirect(url_for('search_campaign'))
    return render_template('Influencer/AdRequests/request.html',campaign=campaign,influencer=influencer)

@app.route('/influencer/adrequest/editrequest/<int:id>/<int:ad_id>',methods=['GET','POST'])
@check_session
def edit_request_adreq(id,ad_id):
    username=session['username']
    user=User.query.filter_by(username=username).first()
    influencer=Influencer.query.filter_by(user_id=user.id).first()
    campaign=Campaign.query.get(id)
    adreq=AdRequest.query.get(ad_id)
    print(campaign.camp_name,adreq.influencer.name)
    print(adreq)
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    if not adreq:
        flash("Ad Request doesn't exist",category="danger")
        return redirect(url_for('adreqs_list',id=id))
    if request.method=='POST':
        influname=request.form.get("influ-name")
        campname=request.form.get("camp-name")
        message=request.form.get("message")
        requirements=request.form.get("requirements")
        pay_amt=request.form.get("amt")
        influencer=Influencer.query.filter_by(name=influname).first()
        campaign=Campaign.query.filter_by(camp_name=campname).first()
        print(influname,campname,message,requirements,pay_amt)
        if not influname or not campname or not message or not requirements or not pay_amt:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('edit_request_adreq',id=id,ad_id=ad_id))
        if not campaign:
            flash("Camapign doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq=AdRequest.query.get(ad_id)
        adreq.requirements=requirements
        adreq.pay_amt=pay_amt
        adreq.message=message
        db.session.commit()
        flash('Ad Request edited successfully',category="success")
        return redirect(url_for('home'))
    return render_template('Influencer/AdRequests/edit.html',campaign=campaign,adreq=adreq)#request_adreq)


@app.route('/influencer/adrequest/deleterequest/<int:id>/<int:ad_id>',methods=['GET','POST'])
@check_session
def delete_request_adreq(id,ad_id):
    campaign=Campaign.query.get(id)
    adreq=AdRequest.query.get(ad_id)
    if request.method=='POST':
        if not campaign:
            flash("Campaign doesn't exist",category="danger")
            return redirect(url_for('home'))
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('adreqs_list',id=id))
        db.session.delete(adreq)
        db.session.commit()
        flash("Ad Request successfully deleted",category="danger")
        return redirect(url_for('home'))
    return render_template('Influencer/AdRequests/delete.html',campaign=campaign,adreq=adreq)


@app.route('/acceptadreq/<int:ad_id>',methods=['GET','POST'])
@check_session
def accept_adreq(ad_id):
    adreq=AdRequest.query.get(ad_id)
    if request.method=="POST":
        adreq=AdRequest.query.get(ad_id)
        print(adreq)
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq.status="accepted"
        db.session.commit()
        flash("Accepted Ad Request",category="success")
        return redirect(url_for('home'))
    return render_template('Influencer/AdRequests/accept.html',a=adreq)

@app.route('/rejectadreq/<int:ad_id>',methods=['GET','POST'])
@check_session
def reject_adreq(ad_id):
    adreq=AdRequest.query.get(ad_id)
    if request.method=="POST":
        adreq=AdRequest.query.get(ad_id)
        print(adreq)
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq.status="rejected"
        db.session.commit()
        flash("Rejected Ad Request",category="danger")
        return redirect(url_for('home'))
    return render_template('Influencer/AdRequests/reject.html',a=adreq)

@app.route('/completeadreq/<int:ad_id>',methods=["POST"])
@check_session
def complete_adreq(ad_id):
    adreq=AdRequest.query.get(ad_id)
    if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('home'))
    adreq.status="completed"
    db.session.commit()
    flash("Marked Ad Request as Complete",category="success")
    
    campaign=adreq.campaign
    campaign_id=campaign.id
    print(campaign.progress)
    completed_adreqs=AdRequest.query.filter_by(camp_id=campaign_id,status="completed").count()
    adreqs= AdRequest.query.filter(
        AdRequest.camp_id == campaign_id,
        AdRequest.status.in_(["completed", "accepted", "pending"])
    ).count()

    print(completed_adreqs,adreqs)
    print(completed_adreqs,adreqs)
    progress=int((completed_adreqs/float(adreqs))*100)
    campaign.progress=progress
    print(progress)
    
    if campaign.progress==100:
        campaign.status="completed"
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/acceptadreqfrominfluencer/<int:ad_id>',methods=['GET','POST'])
@check_session
def accept_adreq_from_influencer(ad_id):
    adreq=AdRequest.query.get(ad_id)
    if request.method=="POST":
        adreq=AdRequest.query.get(ad_id)
        print(adreq)
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq.status="accepted"
        campaign=Campaign.query.filter(adreq.camp_id==Campaign.id).first()
        completed_adreqs=AdRequest.query.filter_by(camp_id=campaign.id,status="completed").count()
        adreqs= AdRequest.query.filter(
                AdRequest.camp_id == campaign.id,
                AdRequest.status.in_(["completed", "accepted", "pending"])
                ).count()
        print(campaign)
        print(completed_adreqs,adreqs)
        print(completed_adreqs,adreqs)
        progress=int((completed_adreqs/float(adreqs))*100)
        print(progress)
        campaign.progress=progress
        db.session.commit()
        flash("Accepted Ad Request",category="success")
        return redirect(url_for('adreqs_list',id=adreq.campaign.id))
    return render_template('Sponsor/AdRequests/accept.html',a=adreq)

@app.route('/rejectadreqfrominfluencer/<int:ad_id>',methods=['GET','POST'])
@check_session
def reject_adreq_from_influencer(ad_id):
    adreq=AdRequest.query.get(ad_id)
    if request.method=="POST":
        adreq=AdRequest.query.get(ad_id)
        print(adreq)
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq.status="rejected"
        db.session.commit()
        flash("Rejected Ad Request",category="danger")
        return redirect(url_for('adreqs_list',id=adreq.campaign.id))
    return render_template('Sponsor/AdRequests/reject.html',a=adreq)

@app.route('/addcampaign')
@check_session
def add_campaign():
    user=User.query.filter_by(username=session['username']).first()
    sponsor=Sponsor.query.filter_by(user_id=user.id).first()
    if not user or not sponsor:
        flash("The account doesn't exist. Please login again!",category="danger")
        return redirect(url_for('login'))
    return render_template('Sponsor/Campaigns/add.html',sponsor=sponsor)


@app.route('/addcampaign/<int:id>',methods=['POST'])
@check_session
def add_campaign_post(id):
    sponsor=Sponsor.query.get(id)
    if not sponsor:
        flash("Sponsor doesn't exist",category="danger")
        return redirect(url_for('register'))
    name=request.form.get("camp-name")
    start_date=request.form.get("start-date")
    end_date=request.form.get("end-date")
    budget=request.form.get("budget")
    niche=request.form.get("camp-niche")
    desc=request.form.get("camp-desc")
    goals=request.form.get("camp-goal")
    visibility=request.form.get("camp-visibility")
    print(visibility)
    if not name or not start_date or not end_date or not budget:
        flash("Please fill all the mandatory fields",category="danger")
        return redirect(url_for('add_campaign'))
    camp=Campaign.query.filter_by(camp_name=name).first()
    if camp:
        flash("Campaign name already exists. Choose another name", category="danger")
        return redirect(url_for('add_campaign'))
    if len(name)>32:
        flash("Name should not exceed 32 characters",category="danger")
        return redirect(url_for('add_campaign'))
    if desc:
        if len(desc)>256:
            flash("Description should not exceed 256 characters",category="danger")
            return redirect(url_for('add_campaign'))
    else:
        desc=None
    if len(goals)>256:
            flash("Goals should not exceed 256 characters",category="danger")
            return redirect(url_for('add_campaign'))
    start_date= datetime.strptime(start_date,"%Y-%m-%d")
    end_date= datetime.strptime(end_date,"%Y-%m-%d")
    if start_date < datetime.now() or end_date < datetime.now():
        flash("Date cannot be in the past",category="danger")
        return redirect(url_for('add_campaign'))
    if end_date < start_date:
        flash("End Date cannot be before Start Date",category="danger")
        return redirect(url_for('add_campaign'))
    campaign=Campaign(camp_name=name,description=desc,start_date=start_date,end_date=end_date,niche=niche,budget=budget,visibility=visibility,goals=goals,sponsor=sponsor)
    db.session.add(campaign)
    db.session.commit()
    flash("Campaign added successfully",category="success")
    return redirect(url_for('home'))


@app.route('/editcampaign/<int:id>',methods=['GET','POST'])
@check_session
def edit_campaign(id):
    campaign=Campaign.query.get(id)
    sponsor=campaign.sponsor
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('register'))
    if request.method=="POST":
        name=request.form.get("camp-name")
        start_date=request.form.get("start-date")
        end_date=request.form.get("end-date")
        budget=request.form.get("budget")
        niche=request.form.get("camp-niche")
        desc=request.form.get("camp-desc")
        goals=request.form.get("camp-goal")
        visibility=request.form.get("camp-visibility")
        if not name or not start_date or not end_date or not budget:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('edit_campaign',id=id))
        if len(name)>32:
            flash("Name should not exceed 32 characters",category="danger")
            return redirect(url_for('edit_campaign',id=id))
        if desc:
            if len(desc)>256:
                flash("Description should not exceed 256 characters",category="danger")
                return redirect(url_for('edit_campaign',id=id))
        else:
            desc=None
        if len(goals)>256:
                flash("Goals should not exceed 256 characters",category="danger")
                return redirect(url_for('edit_campaign',id=id))
        start_date= datetime.strptime(start_date,"%Y-%m-%d")
        end_date= datetime.strptime(end_date,"%Y-%m-%d")
        if start_date < datetime.now() or end_date < datetime.now():
            flash("Date cannot be in the past",category="danger")
            return redirect(url_for('edit_campaign',id=id))
        if end_date < start_date:
            flash("End Date cannot be before Start Date",category="danger")
            return redirect(url_for('edit_campaign',id=id))
        
        campaign.camp_name=name
        campaign.budget=budget
        campaign.niche=niche
        campaign.start_date=start_date
        campaign.end_date=end_date
        campaign.goals=goals
        campaign.description=desc
        campaign.visibility=visibility        
        db.session.commit()
        flash("Campaign edited successfully",category="success")
        return redirect(url_for('home'))
    return render_template("Sponsor/Campaigns/edit.html",c=campaign)

@app.route('/deletecamapign/<int:id>',methods=['GET','POST'])
@check_session
def delete_campaign(id):
    campaign=Campaign.query.get(id)
    if request.method=='POST':
        if not campaign:
            flash("Campaign doesn't exist",category="danger")
            return redirect(url_for('home'))
        db.session.delete(campaign)
        db.session.commit()
        flash("Campaign successfully deleted",category="danger")
        return redirect(url_for('home'))
    return render_template('Sponsor/Campaigns/delete.html',campaign=campaign)


@app.route('/campaign/adrequest/<int:id>',methods=['GET','POST'])
@check_session
def adreqs_list(id):
    campaign=Campaign.query.get(id)
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    req_adreqs=AdRequest.query.filter_by(camp_id=campaign.id,status="requested").all()
    completed_adreqs=AdRequest.query.filter_by(camp_id=campaign.id,status="completed").all()
    other_adreqs=AdRequest.query.filter(
    AdRequest.camp_id == campaign.id,
    AdRequest.status.notin_(["requested", "completed"])
).all()
    return render_template('Sponsor/AdRequests/adreqs_list.html',campaign=campaign,
                           req_adreqs=req_adreqs,other_adreqs=other_adreqs,
                           completed_adreqs=completed_adreqs)

@app.route('/campaign/adrequest/add/<int:id>',methods=['GET','POST'])
@check_session
def add_adreq(id):
    campaign=Campaign.query.get(id)
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    if request.method=='POST':
        influname=request.form.get("influ-name")
        campname=request.form.get("camp-name")
        message=request.form.get("message")
        requirements=request.form.get("requirements")
        pay_amt=request.form.get("amt")
        influencer=Influencer.query.filter_by(name=influname).first()
        campaign=Campaign.query.filter_by(camp_name=campname).first()
        print(influname,campname,message,requirements,pay_amt)
        if not influname or not campname or not message or not requirements or not pay_amt:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('add_adreq',id=id))
        if not influencer:
            flash("Influencer name doesn't exist. Check the spelling or find an influencer",category="danger")
            return redirect(url_for('add_adreq',id=id))
        if not campaign:
            flash("Camapign doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq=AdRequest.query.filter_by(influ_id=influencer.id,camp_id=campaign.id).first()
        if adreq:
            flash("You have already created the ad request",category="danger")
            return redirect(url_for('adreqs_list',id=id))        
        adreq=AdRequest(requirements=requirements, pay_amt=pay_amt, influencer=influencer, campaign=campaign, message=message)
        db.session.add(adreq)
        db.session.commit()
        flash("Ad Request sent successfully",category="success")
        return redirect(url_for('adreqs_list',id=id))
    return render_template('Sponsor/AdRequests/add.html',campaign=campaign)

@app.route('/campaign/adrequest/edit/<int:id>/<int:ad_id>',methods=['GET','POST'])
@check_session
def edit_adreq(id,ad_id):
    campaign=Campaign.query.get(id)
    adreq=AdRequest.query.get(ad_id)
    influencer=adreq.influencer
    print(campaign.camp_name,adreq.influencer.name)
    print(adreq)
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    if not adreq:
        flash("Ad Request doesn't exist",category="danger")
        return redirect(url_for('adreqs_list',id=id))
    if request.method=='POST':
        influname=request.form.get("influ-name")
        campname=request.form.get("camp-name")
        message=request.form.get("message")
        requirements=request.form.get("requirements")
        pay_amt=request.form.get("amt")
        influencer=Influencer.query.filter_by(name=influname).first()
        campaign=Campaign.query.filter_by(camp_name=campname).first()
        print(influname,campname,message,requirements,pay_amt)
        if not influname or not campname or not message or not requirements or not pay_amt:
            flash("Please fill all the mandatory fields",category="danger")
            return redirect(url_for('edit_adreq',id=id,ad_id=ad_id))
        if not influencer:
            flash("Influencer name doesn't exist. Check the spelling or find an influencer",category="danger")
            return redirect(url_for('edit_adreq',id=id,ad_id=ad_id))
        if not campaign:
            flash("Camapign doesn't exist",category="danger")
            return redirect(url_for('home'))
        adreq=AdRequest.query.filter_by(influ_id=influencer.id,camp_id=campaign.id).first()
        # if alr_adreq:
        #     flash("You have already created the ad request",category="danger")
        #     return redirect(url_for('adreqs_list',id=id))        
        adreq=AdRequest.query.get(ad_id)
        adreq.influencer=influencer
        adreq.requirements=requirements
        adreq.pay_amt=pay_amt
        adreq.message=message
        db.session.commit()
        flash('Ad Request edited successfully',category="success")
        return redirect(url_for('adreqs_list',id=id))
    return render_template('Sponsor/AdRequests/edit.html',campaign=campaign,influencer=influencer,adreq=adreq)

@app.route('/adreqcomplete/<int:id>/<int:ad_id>')
@check_session
def adreq_complete(id,ad_id):
    campaign=Campaign.query.get(id)
    adreq=AdRequest.query.get(ad_id)
    if not campaign:
        flash("Campaign doesn't exist",category="danger")
        return redirect(url_for('home'))
    if not adreq:
        flash("Ad Request doesn't exist",category="danger")
        return redirect(url_for('adreqs_list',id=id))
    adreq.status="completed"
    db.session.commit()
    flash('Ad Request completed successfully',category="success")
    return redirect(url_for('adreqs_list',id=id))


@app.route('/deleteadreq/<int:id>/<int:ad_id>',methods=['GET','POST'])
@check_session
def delete_adreq(id,ad_id):
    campaign=Campaign.query.get(id)
    adreq=AdRequest.query.get(ad_id)
    if request.method=='POST':
        if not campaign:
            flash("Campaign doesn't exist",category="danger")
            return redirect(url_for('home'))
        if not adreq:
            flash("Ad Request doesn't exist",category="danger")
            return redirect(url_for('adreqs_list',id=id))
        db.session.delete(adreq)
        db.session.commit()
        flash("Ad Request successfully deleted",category="danger")
        return redirect(url_for('adreqs_list',id=campaign.id))
    return render_template('Sponsor/AdRequests/delete.html',campaign=campaign,adreq=adreq)


@app.route('/users')
@check_admin
def user_list():
    users=User.query.all()
    notflag_users = User.query.filter_by(is_flagged=False).all()
    flag_users=User.query.filter_by(is_flagged=True).all()
    return render_template('Admin/users.html',users=users, notflag_users=notflag_users,flag_users=flag_users)

@app.route('/flaguser/<int:id>',methods=['POST'])
@check_admin
def flag_user(id):
    user=User.query.get(id)
    if not user:
        flash("Cannot flag user which doesn't exist",category="danger")
        return redirect(url_for('home'))
    if user.is_admin:
        flash("Cannot flag admin",category="danger")
        return redirect(url_for('home'))
    user.is_flagged=True
    db.session.commit()
    flash("User has been flagged successfully",category="danger")
    return redirect(url_for('user_list'))

@app.route('/unflaguser/<int:id>',methods=['POST'])
@check_admin
def unflag_user(id):
    user=User.query.get(id)
    if not user:
        flash("Cannot unflag user which doesn't exist",category="danger")
        return redirect(url_for('home'))
    user.is_flagged=False
    db.session.commit()
    flash("User has been unflagged successfully",category="success")
    return redirect(url_for('user_list'))

@app.route('/campaigns')
@check_admin
def campaign_list():
    campaigns=Campaign.query.all()
    notflag_campaigns = Campaign.query.filter_by(is_flagged=False).all()
    flag_camapigns=Campaign.query.filter_by(is_flagged=True).all()
    print(notflag_campaigns)
    return render_template('Admin/campaigns.html',campaigns=campaigns, notflag_campaigns=notflag_campaigns,flag_campaigns=flag_camapigns)

@app.route('/flagcampaign/<int:id>',methods=['POST'])
@check_admin
def flag_campaign(id):
    campaign=Campaign.query.get(id)
    print(campaign)
    if not campaign:
        flash("Cannot flag camapign which doesn't exist",category="danger")
        return redirect(url_for('home'))
    campaign.is_flagged=True
    db.session.commit()
    flash("Campaign has been flagged successfully",category="danger")
    return redirect(url_for('campaign_list'))

@app.route('/unflagcamapign/<int:id>',methods=['POST'])
@check_admin
def unflag_campaign(id):
    campaign=Campaign.query.get(id)
    if not campaign:
        flash("Cannot unflag camapign which doesn't exist",category="danger")
        return redirect(url_for('home'))
    campaign.is_flagged=False
    db.session.commit()
    flash("Campaign has been unflagged successfully",category="success")
    return redirect(url_for('campaign_list'))


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('login'))


@app.route('/statistics')
@check_session
def stats():
    user=User.query.filter_by(username=session['username']).first()
    if user.role=="Sponsor":
        sponsor=Sponsor.query.filter_by(user_id=user.id).first()
        if not sponsor:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        campaigns=Campaign.query.filter_by(spo_id=sponsor.id, is_flagged=False).all()
        active_campaigns=Campaign.query.filter_by(spo_id=sponsor.id, is_flagged=False,status="active").all()
        completed_campaigns=Campaign.query.filter_by(spo_id=sponsor.id, is_flagged=False,status="completed").all()
        adreqs=[adreq for campaign in campaigns for adreq in campaign.adreqs]
        statuses = ["pending", "requested", "accepted", "rejected", "completed"]
        status_counts = Counter() 
        for adreq in adreqs:
            if adreq.status in statuses:
                status_counts[adreq.status] += 1
        data_counts = [status_counts[status] for status in statuses]
        print(data_counts)
        return render_template("chart.html",user=user,sponsor=sponsor,active_campaigns=active_campaigns, campaigns=campaigns,
                               completed_campaigns=completed_campaigns,adreqs=adreqs,data_counts=data_counts)
    elif user.role=="Influencer":
        influencer=Influencer.query.filter_by(user_id=user.id).first()
        if not influencer:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        adreqs=[adreq  for adreq in influencer.adreqs]
        statuses = ["requested", "accepted", "rejected", "completed"]
        status_counts = Counter() 
        for adreq in adreqs:
            if adreq.status in statuses:
                status_counts[adreq.status] += 1
        data_counts = [status_counts[status] for status in statuses]
        earnings_data=defaultdict(float)
        earnings_adreqs=AdRequest.query.filter_by(influ_id=influencer.id,status="completed").all()
        for adreq in earnings_adreqs:
            campaign_name = adreq.campaign.camp_name  # Replace with actual attribute accessing campaign's name
            earnings_data[campaign_name] += adreq.pay_amt

        campaign_names = list(earnings_data.keys())
        earnings_data = list(earnings_data.values())
        return render_template("chart.html",user=user,influencer=influencer,adreqs=adreqs,data_counts=data_counts,earnings_data=earnings_data,
                               campaign_names=campaign_names,earnings_adreqs=earnings_adreqs)
    
    elif user.role=="Admin":
        if not user:
            flash("You need to login first",category="danger")
            return redirect(url_for('login'))
        users=User.query.all()
        campaigns=Campaign.query.all()
        notflag_users = User.query.filter_by(is_flagged=False).all()
        flag_users=User.query.filter_by(is_flagged=True).all()
        notflag_campaigns = Campaign.query.filter_by(is_flagged=False).all()
        flag_campaigns=Campaign.query.filter_by(is_flagged=True).all()
        sponsors=Sponsor.query.all()
        adreqs=AdRequest.query.all()
        statuses = ["pending", "requested", "accepted", "rejected", "completed"]
        status_counts = Counter() 
        for adreq in adreqs:
            if adreq.status in statuses:
                status_counts[adreq.status] += 1
        data_counts = [status_counts[status] for status in statuses]
        print(data_counts)
        return render_template('chart.html',user=user,users=users,campaigns=campaigns,flag_users=flag_users,
                               notflag_users=notflag_users,notflag_campaigns=notflag_campaigns,
                               flag_campaigns=flag_campaigns,sponsors=sponsors,data_counts=data_counts)
    return render_template('/chart.html')
    

@app.route('/profile',methods=['GET','POST'])
@check_session
def profile():
    username=session['username']
    user=User.query.filter_by(username=username).first()
    if not user:
        flash("Login first",category="danger")
        return redirect(url_for('login'))
    
    if user.role=="Influencer":
        influencer=Influencer.query.filter_by(user_id=user.id).first()
        profile_pic=url_for('static',filename='profile_pics/' + user.profile_pic)
        adreqs=(AdRequest.query
                .join(Influencer, AdRequest.influ_id == Influencer.id)
                .join(Campaign, AdRequest.camp_id == Campaign.id)
                .filter(AdRequest.status.in_(["completed", "accepted"]),Influencer.id==influencer.id)
                .all())
        print(adreqs)
        return render_template('profile.html',user=user,influencer=influencer,
                               profile_pic=profile_pic,adreqs=adreqs)
    if user.role=="Sponsor":
        sponsor=Sponsor.query.filter_by(user_id=user.id).first()
        profile_pic=url_for('static',filename='profile_pics/' + user.profile_pic)
        print(profile_pic)
        return render_template('profile.html',user=user,sponsor=sponsor,profile_pic=profile_pic)
    if user.role=="Admin":
        admin=User.query.filter_by(is_admin=True).first()
        profile_pic=url_for('static',filename='profile_pics/' + user.profile_pic)
        return render_template('profile.html',user=user,admin=admin,profile_pic=profile_pic)

@app.route('/profilepic/<int:id>',methods=['GET',"POST"])
@check_session
def upload_pic(id):
    user=User.query.get(id) #since id is primary key, it will directly search for that
    curr_user=User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID",category="danger")
        return redirect(url_for('login'))
    if user.username != session['username']:
        session.pop('username')
        flash("Not authorized to perform this action!",category="danger")
        return redirect(url_for('login'))
    
    if request.method=="POST":
        profile=request.files['profile_pic']
        if not profile:
            flash("Please upload a file to change the profile picture",category="danger")
            return redirect(url_for('profile'))
        
        # Validate the uploaded file to be only image type files
        if what(profile) not in ['jpeg', 'png', 'gif', 'bmp']:
            flash("Only image files are allowed!", category="danger")
            return redirect(url_for('profile'))
        
        uploadpath="static\\profile_pics"
        filename=secure_filename(curr_user.username+"_"+str(datetime.now().time())+"_"+profile.filename)
        profile.save(os.path.join(uploadpath,filename))
        final_path=filename
        try:
            user.profile_pic=final_path
            db.session.commit()
            flash('Added profile picture successfully',category="success")
            return redirect(url_for('profile'))
        except Exception as e:
            flash("Something went wrong while adding post",category="danger")
            return redirect(url_for('profile'))


@app.route('/users/<int:id>/update',methods=["POST"])
@check_session
def update_profile(id):
    user=User.query.get(id) #since id is primary key, it will directly search for that
    curr_user=User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID",category="danger")
        return redirect(url_for('login'))
    if user.username != session['username']:
        session.pop('username')
        flash("Not authorized to perform this action!",category="danger")
        return redirect(url_for('login'))
    if curr_user.is_admin:
        flash("Admin cannot update their own profile through this!",category="danger")
        return redirect(url_for('profile'))
    if request.method=="POST":
        if user.role=="Influencer":
            influencer=Influencer.query.filter_by(user_id=user.id).first()
            name=request.form.get('name')
            about=request.form.get('about')
            niche=request.form.get('niche')
            reach=request.form.get('reach')
            category=request.form.get('category')
            platform=request.form.get('platform')
            print(name,user.id)
            
            if not name or not category or not platform:
                flash("Please fill all the fields",category="danger")
                return redirect(url_for('profile'))
            if len(name) > 32:
                flash("Name should not be longer 32 characters ",category="danger")
                return redirect(url_for('profile'))
            if niche and len(niche) > 256:
                flash("Niche should not be longer 256 characters ",category="danger")
                return redirect(url_for('profile'))
            if not niche:
                niche=None
            if len(platform) > 64:
                flash("Platfrom should not be longer 64 characters ",category="danger")
                return redirect(url_for('profile'))
            if about and len(about)>256:
                flash("About should not be longer 256 characters ",category="danger")
                return redirect(url_for('profile'))

            influencer.name=name
            influencer.about=about
            influencer.niche=niche
            influencer.reach=reach
            influencer.category=category
            influencer.platform=platform
            db.session.commit()
            flash("Profile updated successfully",category="success")
            return redirect(url_for('profile'))
        if user.role=="Sponsor":
            sponsor=Sponsor.query.filter_by(user_id=user.id).first()
            name=request.form.get('name')
            industry=request.form.get('industry')
            budget=request.form.get('budget')

            if not name or not industry or not budget:
                flash("Please fill all the fields",category="danger")
                return redirect(url_for('profile'))
            if len(name) > 32:
                flash("Name should not be longer 32 characters ",category="danger")
                return redirect(url_for('profile'))
            sponsor.name=name
            sponsor.industry=industry
            sponsor.budget=budget
            db.session.commit()
            flash("Profile updated successfully",category="success")
            return redirect(url_for('profile'))
    return redirect(url_for('profile'))

@app.route('/users/<int:id>/change_pass',methods=["POST"])
@check_session
def change_pass(id):
    user=User.query.get(id) #since id is primary key, it will directly search for that
    curr_user=User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID",category="danger")
        return redirect(url_for('login'))
    if user.username != session['username']:
        session.pop('username')
        flash("Not authorized to perform this action!",category="danger")
        return redirect(url_for('login'))
    if request.method=="POST":
        curr_pass=request.form.get('password')
        new_pass=request.form.get('npassword')
        conf_pass=request.form.get('confpassword')
        if not curr_pass or not new_pass or not conf_pass:
            flash("Fill in all the required fields. Please try again",category="danger")
            return redirect(url_for('profile'))
        if not check_password_hash(user.passhash,curr_pass):
            flash("Current password is wrong. Please try again",category="danger")
            return redirect(url_for('profile'))
        if not (new_pass==conf_pass):
            flash("Confirm new password is wrong. Please try again",category="danger")
            return redirect(url_for('profile'))
        new_passhash=generate_password_hash(new_pass)
        user.passhash=new_passhash
        db.session.commit()
        flash("Password successfully changed",category="success")
        return redirect(url_for('profile'))
            
@app.route('/users/<int:id>/delete',methods=["POST"])
@check_session
def delete_user(id):
    user=User.query.get(id) #since id is primary key, it will directly search for that
    curr_user=User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID",category="danger")
        return redirect(url_for('login'))
    if user.username != session['username'] and not curr_user.is_admin:
        session.pop('username')
        flash("Not authorized to perform this action!",category="danger")
        return redirect(url_for('profile'))
    if user.is_admin:
        flash("You cannot delete an admin",category="danger")
        return redirect(url_for('profile'))

    db.session.delete(user)
    db.session.commit()
    flash("Deletion successful",category="danger")
    return redirect(url_for('login'))
