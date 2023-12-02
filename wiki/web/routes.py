"""
    Routes
    ~~~~~~
"""
import os.path

from flask import Blueprint, jsonify, session, send_file
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.utils import secure_filename

from wiki.core import Processor
from wiki.web import current_users, user
from wiki.web import current_wiki
from wiki.web.forms import EditorForm, SignUpForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web.user import *

bp = Blueprint('wiki', __name__, static_folder='static', static_url_path='/static')
img = os.path.join(bp.static_folder, 'Images')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
@protect
def home():
    user_name = session["unique_id"]
    if User.is_authenticated:
        page = current_wiki.get(user_name + '-' + 'home')
        if page:
            return display(user_name + '-' + 'home')
        return render_template('home.html')
    return redirect(url_for('user_login'))


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


# function used to display profile page
@bp.route('/profile')
@protect
def profile():
    user_name = session["unique_id"]
    all_pages = current_wiki.get_all()
    bio_page = current_wiki.get(user_name + '-' +'bio')
    if bio_page:
        return display(user_name + '-' + 'bio', pages_sent_by_author=all_pages)
    return render_template('bio.html')


@bp.route('/<path:url>/')
@protect
def display(url, pages_sent_by_author=None):
    page = current_wiki.get_or_404(url)

    user_name = session["unique_id"]
    file_extension = search_file_in_directory(img, url)

    if file_extension:
        page_image = f"{url}{file_extension}"
    else:
        page_image = ''

    if url == 'home':
        return render_template('page.html', page=page, image=page_image)
    elif url == 'bio':
        page_bio = current_wiki.get_or_404(url)
        return render_template('page_bio.html', page=page_bio, pages_sent=pages_sent_by_author, image=page_image)
    return render_template('page.html', page=page, image=page_image)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


def search_file_in_directory(directory, filename):
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Compare filenames without extensions
            if os.path.splitext(file)[0] == os.path.splitext(filename)[0]:
                file_extension = os.path.splitext(file)[1]
                return file_extension
    return None


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    user_name = session["unique_id"]

    file_extension = search_file_in_directory(img, user_name + '-' + url)

    if file_extension:
        page_image = f"{user_name}-{url}{file_extension}"
    else:
        page_image = ''

    if not page:
        page = current_wiki.get_bare(url)

    form = EditorForm(obj=page)

    # Initialize form with page data
    if form.validate_on_submit():
        form.populate_obj(page)

        upload_image = form.image.data
        if upload_image and allowed_file(upload_image.filename):
            file = upload_image

            original_file_name = secure_filename(file.filename)
            file_extension = original_file_name.split('.', 1)[-1]
            new_file_name = f"{url}.{file_extension}"

            file.save(os.path.join(img, new_file_name))
            flash('Image uploaded successfully!', 'success')
        elif upload_image is None:
            pass
        else:
            flash('Invalid file type. Allowed types are png, jpg, jpeg.', 'error')

        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page, image=page_image)



@bp.route('/save/<path:url>/', methods=['POST'])
@protect
def save(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)

    if request.method == 'POST':
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        return jsonify(success=True)
    return jsonify("success=False, errors=form.errors")


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        new_url = form.url.data
        current_wiki.move(url, new_url)

        file_extension = search_file_in_directory(img, url)
        old_image_path = os.path.join(img,f"{url}{file_extension}")
        new_image_path = os.path.join(img,f"{new_url}{file_extension}")

        os.rename(old_image_path, new_image_path)

        return redirect(url_for('wiki.display', url=new_url))
    return render_template('move.html', form=form, page=page)


@bp.route('/download_image/<path:url>/')
@protect
def download_image(url):
    user_name = session["unique_id"]

    file_extension = search_file_in_directory(img, url)


    page_image = f"{url}{file_extension}"

    image_path = os.path.join(img, page_image)


    # Set the filename that the user will see when downloading
    filename = page_image

    return send_file(image_path, as_attachment=True, download_name=filename)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        if form.search_by_author.data:

            results = current_wiki.search_by_author(form.term.data)
        else:
            results = current_wiki.search(form.term.data, form.ignore_case.data)

        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        session["unique_id"] = form.name.data
        login_user(user)
        user.set('authenticated', True)
        session['is_authenticated'] = True
        flash(f'Login successful, {form.name.data}!', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        if form.password.data == form.confirm_password.data:
            user_manager = UserManager()
            # Check if the username already exists
            if user_manager.user_exists(form.name.data):
                flash('Username already exists. Please choose a different username.', 'danger')
            else:
                user_manager.add_user(form.name.data, form.password.data)

                flash('Account created successfully. You can now log in.', 'success')
                return redirect(url_for('wiki.user_login'))
    return render_template('signup.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    session['is_authenticated'] = False
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    return render_template('signup.html')


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404