from datetime import datetime
from blog import db, app, login_manager
from flask_login import UserMixin
from sqlalchemy import event

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255))
    dn = db.Column(db.String(255), unique=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def __init__(self, dn, username):
        self.dn = dn
        self.username = username

    def __repr__(self):
        return self.dn

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    print(f"Loading user. User ID: {user_id}, User: {user}, Users in DB: {User.query.all()}")
    return user


class Paper(db.Model):
    __searchable__ = ['author', 'title', 'joural', 'year', 'type', 'doi',
                      'keywords', 'abstract', 'license', 'publisher',
                      'ranking', 'volume']
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    journal = db.Column(db.String, nullable=True)
    year = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String, nullable=True)
    doi = db.Column(db.String, nullable=True)
    arxiv = db.Column(db.String, nullable=True)
    url = db.Column(db.String, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    license = db.Column(db.String, nullable=True)
    publisher = db.Column(db.String, nullable=True)
    ranking = db.Column(db.String, nullable=True)
    volume = db.Column(db.String, nullable=True)
    filename = db.Column(db.String, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    user = db.relationship('User', backref=db.backref('papers', lazy=True))

    def __repr__(self):
        return f"Paper('{self.title}', '{self.date_posted}')"


@event.listens_for(Paper, 'before_delete')
def before_delete_paper(mapper, connection, target):
    # Delete associated PRR records when a Paper is deleted
    PRR.query.filter_by(paper_id=target.id).delete()
    Favorite.query.filter_by(paper_id=target.id).delete()


class PRR(db.Model):
    __searchable__ = []
    id = db.Column(db.Integer, primary_key=True)
    presenter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    room = db.Column(db.String, nullable=False)
    time = db.Column(db.Time, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    user = db.relationship('User', backref=db.backref('prrs', lazy=True), foreign_keys=[user_id])
    presenter = db.relationship('User', foreign_keys=[presenter_id])
    paper = db.relationship('Paper', foreign_keys=[paper_id])

    def __repr__(self):
        return f"PRR('{self.presenter.username}', '{self.paper.title}', '{self.date_posted}')"

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    paper = db.relationship('Paper', foreign_keys=[paper_id])
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()
