from flask import Flask,render_template,request, redirect, session, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app=Flask(__name__)

import config

import models

import routes



