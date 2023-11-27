"""
    Routes
    ~~~~~~
"""
from flask import Blueprint, jsonify
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from wiki.core import Processor
from wiki.web.forms import EditorForm, SignUpForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
from wiki.web.user import UserManager

bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')

@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)

# function used to display profile page
@bp.route('/profile')
@protect
def profile():
    pages = current_wiki.get_all()
    page = current_wiki.get('bio')
    if page:
        return display('bio', pages_sent_by_author=pages)
    return render_template('bio.html')

@bp.route('/<path:url>/')
@protect
def display(url, pages_sent_by_author=None):
    page = current_wiki.get_or_404(url)
    # Determine which template to use based on the URL
    if url == 'home':
        return render_template('page.html', page=page)
    elif url == 'bio':
        page_bio = current_wiki.get(url)
        if not page_bio:
            return render_template('bio.html', page=page_bio, pages_sent=pages_sent_by_author)
        return render_template('page_bio.html', page=page_bio, pages_sent=pages_sent_by_author)
    return render_template('page.html', page=page, pages_sent=pages_sent_by_author)

@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)



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
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


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
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
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
