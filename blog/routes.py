import os
from flask import render_template, jsonify, url_for, flash, redirect, request, abort, send_from_directory, send_file, \
    session
from blog import app, db
from blog.global_ldap_authentication import *
from blog.forms import PaperForm, LoginForm, PRRForm
from flask_login import login_user, current_user, logout_user, login_required
from blog.models import Paper, User, PRR, Favorite
from blog.bibtexGen import BibTexFetcher
from werkzeug.utils import secure_filename
from datetime import datetime


@app.route("/")
def home():
    current_date = datetime.utcnow().date()
    next_prr = PRR.query.filter(PRR.date >= current_date).order_by(PRR.date).first()
    if current_user.is_authenticated:
        user_total_papers = len(current_user.papers)
        latest_addition = Paper.query.filter_by(user_id=current_user.username).order_by(
            Paper.date_posted.desc()).first()
        return render_template("home.html", user_total_papers=user_total_papers,
                               latest_addition=latest_addition, next_prr=next_prr)
    else:
        return render_template("home.html", next_prr=next_prr)


@app.route("/papers")
def papers():
    papers = Paper.query.order_by(Paper.date_posted.desc())
    return render_template('papers.html', papers=papers)


@app.route("/paper/<int:paper_id>", methods=['GET', 'POST'])
def paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    form = PaperForm()
    if current_user.is_authenticated:
        paper_in_favorites = Favorite.query.filter_by(user_id=current_user.id, paper_id=paper.id).first() is not None
    else:
        paper_in_favorites = None

    return render_template('paper.html', paper=paper, form=form, paper_in_favorites=paper_in_favorites)


@app.route("/faq")
def faq():
    return render_template('about.html', title='About')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        login_id = "rz.fh-ingolstadt.de\%s" % form.user_name_pid.data
        login_username = form.user_name_pid.data
        login_password = form.user_pid_Password.data
        login_msg = global_ldap_authentication(login_id, login_password)
        user_uid = global_ldap_authentication_uid(login_id, login_password, login_username)

        if user_uid == "Fail!":
            flash('LDAP Authentication Failed. Please check your credentials.', 'danger')
            return render_template('login.html', title='Login', form=form)

        user = User.query.filter_by(username=login_username).first()
        if not user:
            # Create a new user if not exists
            user = User(username=login_username, dn=user_uid)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        print("User ID after login:", current_user.get_id())
        print("Is authenticated after login:", current_user.is_authenticated)
        flash("Authentication Success", 'success')
        return redirect(url_for('home'))

    # Add a return statement for the case where the user is already authenticated
    return render_template('login.html', title='Login', form=form)


@app.route('/test')
def test():
    print(f"User ID in test route: {current_user.get_id()}")
    print(f"Is authenticated in test route: {current_user.is_authenticated}")
    return render_template('home.html', title='Test')


@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Logout Success", 'info')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Your existing imports...

@app.route("/paper/new", methods=['GET', 'POST'])
@login_required
def new_paper():
    form = PaperForm()
    exists = db.session.query(Paper.title).filter_by(title=form.title.data, author=form.author.data).first() is not None

    if form.validate_on_submit():
        doi = form.doi.data
        arxiv = form.arxiv.data

        file = form.file.data
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Check if the entry already exists
        if not exists:
            # Manually create a Paper instance with the data from the form
            post = Paper(
                title=form.title.data,
                author=form.author.data,
                journal=form.journal.data,
                year=form.year.data,
                type=form.type.data,
                doi=form.doi.data,
                arxiv=form.arxiv.data,
                url=form.url.data,
                comments=form.comments.data,
                keywords=form.keywords.data,
                abstract=form.abstract.data,
                license=form.license.data,
                publisher=form.publisher.data,
                ranking=form.ranking.data,
                volume=form.volume.data,
                user=current_user,
                filename=filename
            )

            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('papers'))
        else:
            flash('The paper already exists!', 'danger')

        if form.validate_on_submit() and not exists:
            # Check which field the user filled
            if doi or arxiv:
                getbib = BibTexFetcher()
                bibtex_data = getbib.getbib(doi=doi, arxiv=arxiv)
            else:
                # If neither DOI nor arXiv is provided, set bibtex_data to an empty dictionary
                bibtex_data = {}

            # Update form fields with BibTeX data
            form.title.data = bibtex_data.get('title', '')
            form.journal.data = bibtex_data.get('booktitle',
                                                '')  # Assuming 'booktitle' corresponds to the journal field
            form.year.data = int(bibtex_data.get('year', '')) if bibtex_data.get('year') else None
            form.author.data = bibtex_data.get('author', '')
            form.url.data = bibtex_data.get('url', '')
            form.publisher.data = bibtex_data.get('publisher', '')
            form.type.data = bibtex_data.get('type', '')  # Update as needed
            form.doi.data = bibtex_data.get('doi', '')  # Update as needed
            form.abstract.data = bibtex_data.get('abstract', '')  # Update as needed
            # Update other fields accordingly...

            # Check if the BibTeX data is not available
            if not bibtex_data:
                # Manually create a Paper instance with the data from the form
                post = Paper(
                    title=form.title.data,
                    author=form.author.data,
                    journal=form.journal.data,
                    year=form.year.data,
                    type=form.type.data,
                    doi=form.doi.data,
                    arxiv=form.arxiv.data,
                    url=form.url.data,
                    comments=form.comments.data,
                    keywords=form.keywords.data,
                    abstract=form.abstract.data,
                    license=form.license.data,
                    publisher=form.publisher.data,
                    ranking=form.ranking.data,
                    volume=form.volume.data,
                    user=current_user
                )

                db.session.add(post)
                db.session.commit()
                flash('Your post has been created!', 'success')
                return redirect(url_for('papers'))
        else:
            flash('The paper already exists!', 'danger')

    return render_template('create_post.html', title='New Paper', form=form, legend='New Paper')


@app.route("/paper/new/ajax", methods=['POST'])
def new_paper_ajax():
    data = request.get_json()
    doi = data.get('doi', '')
    arxiv = data.get('arxiv', '')

    getbib = BibTexFetcher()
    if doi:
        bibtex_data = getbib.getbib(doi=doi)
    elif arxiv:
        bibtex_data = getbib.getbib(arxiv=arxiv)
    else:
        bibtex_data = {}
    print(bibtex_data)
    return jsonify(bibtex_data)


@app.route("/paper/<int:paper_id>/update", methods=['GET', 'POST'])
@login_required
def update_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)

    if current_user != paper.user:
        abort(403)

    form = PaperForm()

    if form.validate_on_submit():
        paper.title = form.title.data,
        paper.author = form.author.data,
        paper.journal = form.journal.data,
        paper.year = form.year.data,
        paper.type = form.type.data,
        paper.doi = form.doi.data,
        paper.arxiv = form.arxiv.data,
        paper.url = form.url.data,
        paper.comments = form.comments.data,
        paper.keywords = form.keywords.data,
        paper.abstract = form.abstract.data,
        paper.license = form.license.data,
        paper.publisher = form.publisher.data,
        paper.ranking = form.ranking.data,
        paper.volume = form.volume.data
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            if paper.filename != None:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.filename))
            filename = secure_filename(file.filename)
            paper.filename = filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.session.commit()
        else:
            db.session.commit()
        flash('Paper updated successfully!', 'success')
        return redirect(url_for('paper', paper_id=paper.id))
    elif request.method == 'GET':
        form.title.data = paper.title,
        form.author.data = paper.author,
        form.journal.data = paper.journal,
        form.year.data = paper.year,
        form.type.data = paper.type,
        form.doi.data = paper.doi,
        form.arxiv.data = paper.arxiv,
        form.url.data = paper.url,
        form.comments.data = paper.comments,
        form.keywords.data = paper.keywords,
        form.abstract.data = paper.abstract,
        form.license.data = paper.license,
        form.publisher.data = paper.publisher,
        form.ranking.data = paper.ranking,
        form.volume.data = paper.volume

    return render_template('create_post.html', title='Update Paper', form=form,
                           paper=paper, legend='Update Paper')


@app.route("/paper/<int:paper_id>/delete", methods=['POST'])
@login_required
def delete_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    if current_user != paper.user:
        abort(403)
    if paper.filename != None:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], paper.filename))
    db.session.delete(paper)
    db.session.commit()
    flash('Paper deleted successfully!', 'success')
    return redirect(url_for('papers'))


@app.route('/paper/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    print('Here i am')
    if filename != None:
        uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        print('Uploads Directory:', uploads)
        file_path = os.path.join(uploads, filename)
        print('File Path:', file_path)
        return send_from_directory(uploads, filename, as_attachment=True)
    else:
        abort(404)


@app.route("/prrs")
def prrs():
    page = request.args.get('page', 1, type=int)
    prrs = PRR.query.order_by(PRR.date_posted.desc())
    return render_template('prrs.html', prrs=prrs)


@app.route("/prr/new", methods=['GET', 'POST'])
@login_required
def new_prr():
    print("Reached new_prr route")
    form = PRRForm()

    if form.validate_on_submit():
        try:
            print(f"Date: {form.date.data}")
            print(f"Presenter ID: {form.presenter.data}")
            print(f"Paper ID: {form.paper.data}")

            # Retrieve User and Paper objects based on the selected IDs
            presenter_user = User.query.get(form.presenter.data)
            paper_obj = Paper.query.get(form.paper.data)

            post = PRR(
                date=form.date.data,
                time=form.time.data,
                presenter=presenter_user,
                paper=paper_obj,
                user=current_user,
                room=form.room.data
            )

            db.session.add(post)
            db.session.commit()
            flash('Your PRR has been created!', 'success')
            return redirect(url_for('prrs'))
        except Exception as e:
            print(f"Error creating PRR: {e}")
            db.session.rollback()
            flash('Error creating PRR. Please try again.', 'danger')

    return render_template('create_prr.html', title='New PRR', form=form, legend='New PRR')


@app.route("/prr/<int:prr_id>/delete", methods=['POST'])
@login_required
def delete_prr(prr_id):
    prr = PRR.query.get_or_404(prr_id)
    if prr.presenter_id != current_user.id:
        abort(403)  # Forbidden, as the current user doesn't own this PRR
    db.session.delete(prr)
    db.session.commit()
    flash('Your PRR has been deleted!', 'success')
    return redirect(url_for('prrs'))



@app.route('/toggle_favorite/<int:paper_id>', methods=['POST'])
@login_required
def toggle_favorite(paper_id):
    paper = Paper.query.get_or_404(paper_id)

    # Check if the paper is in favorites
    if Favorite.query.filter_by(user_id=current_user.id, paper_id=paper.id).first():
        # Paper is in favorites, remove it
        favorite = Favorite.query.filter_by(user_id=current_user.id, paper_id=paper.id).first()
        db.session.delete(favorite)
        db.session.commit()
        flash('Paper removed from favorites!', 'success')
    else:
        # Paper is not in favorites, add it
        favorite = Favorite(user_id=current_user.id, paper_id=paper.id)
        db.session.add(favorite)
        db.session.commit()
        flash('Paper added to favorites!', 'success')

    return redirect(url_for('paper', paper_id=paper.id))


@app.route("/favorites")
@login_required
def favorites():
    user_favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=user_favorites)
