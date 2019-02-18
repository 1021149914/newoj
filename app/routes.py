from flask import render_template, flash, redirect, url_for, request, jsonify, Response
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddProblem, Commit, AddInform, AddContest
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Problem, Contest, Inform, Record, Contest_Problem
from werkzeug.urls import url_parse
from datetime import datetime
from sqlalchemy import desc
from flask_paginate import Pagination, get_page_parameter
import os, json


@app.route('/')
@app.route('/index')
@login_required
def index():
    post=[]
    page = request.args.get('page', 1, type=int)
    posts = Inform.query.paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('problem', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('problem', page=posts.prev_num) \
        if posts.has_prev else None
    post = posts.items
    return render_template('index.html', title='Home', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@app.route('/contest', methods=['GET', 'POST'])
def contest():
    post=[]
    page = request.args.get('page', 1, type=int)
    posts = Contest.query.paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('contest', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('contest', page=posts.prev_num) \
        if posts.has_prev else None
    post = posts.items
    return render_template('contest.html', title='Contest', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@app.route('/contest_problem/<id>', methods=['GET', 'POST'])
def contest_problem(id):
    post = []
    posts = Contest_Problem.query.filter_by(contest_id = id).all()
    for p in posts :
        tmp = {}
        tmp['id'] = p.problem_id
        problem = Problem.query.filter_by(id = p.problem_id).first_or_404()
        tmp['title'] = problem.title
        tmp['source'] = problem.source
        post.append(tmp)
    contest = Contest.query.filter_by(id = id).first_or_404()
    cc = {}
    cc['id'] = id
    cc['title'] =contest.title
    return render_template('contest_problem.html', title='Contest Problem', posts = post, cc = cc)

@login_required
@app.route('/show_code/<id>', methods=['GET', 'POST'])
def show_code(id):
    record = Record.query.filter_by(id=id).first_or_404()
    user = User.query.filter_by(id=record.user_id).first_or_404()
    problem = Problem.query.filter_by(id=record.problem_id).first_or_404()
    return render_template('show_code.html', title='Code', posts = record, author = user, problem = problem)

@login_required
@app.route('/addcontest', methods=['GET', 'POST'])
def addcontest():
    form = AddContest()
    if form.validate_on_submit():
        contest = Contest(title = form.title.data, source = form.source.data, content = form.content.data)
        db.session.add(contest)
        db.session.commit()
        flash('Your contest have been added. Please add problem.')
        return redirect(url_for('addcontestproblem', id=contest.id))
    return render_template('addcontest.html', title='AddContest', form = form)

@login_required
@app.route('/addcontestproblem/<id>', methods=['GET', 'POST'])
def addcontestproblem(id):
    posts = {}
    contest = Contest.query.filter_by(id=id).first_or_404()
    posts['id'] = str(id)
    posts['title'] = contest.title
    cp = Contest_Problem.query.filter_by(contest_id=id).all()
    cot = []
    for c in cp:
        tmp = {}
        tmp['pid'] = c.id
        tmp['id'] = c.problem_id
        p = Problem.query.filter_by(id = c.problem_id).first_or_404()
        tmp['title'] = p.title
        tmp['source'] = p.source
        cot.append(tmp)
    return render_template('addcontestproblem.html', title='Add Contest Problem', posts = posts,cot = cot)

@app.route('/rank', methods=['GET', 'POST'])
def rank():
    

@login_required
@app.route('/pid/<id>', methods=['GET', 'POST'])
def pid(id):
    data = request.get_data().decode()  # 获取post过来的信息
    data = data[11:]
    data_res = json.loads(data)  # 解析json数据
    problem_id = data_res
    p = Problem.query.filter_by(id=problem_id).all()
    if(len(p)>0):
        cp = Contest_Problem(contest_id = id, problem_id = problem_id)
        db.session.add(cp)
        db.session.commit()
        flash('Your problem have been added to the contest.')
        return redirect(url_for('addcontestproblem', id = id))
    else :
        flash('The problem is not available.')
        return redirect(url_for('addcontestproblem', id = id))

@login_required
@app.route('/delet/<id>', methods=['GET', 'POST'])
def delet(id):
    cp = Contest_Problem.query.filter_by(id=id).first_or_404()
    contest_id = cp.contest_id
    db.session.delete(cp)
    db.session.commit()
    flash('The problem has been deleted.')
    return redirect(url_for('addcontestproblem', id = contest_id))

@login_required
@app.route('/addinform', methods=['GET', 'POST'])
def addinform():
    form = AddInform()
    if form.validate_on_submit():
        inform = Inform(title = form.title.data, source = form.source.data, content = form.content.data)
        db.session.add(inform)
        db.session.commit()
        flash('Your announcement have been commited.')
        return redirect(url_for('status'))
    return render_template('addinform.html', title='AddInfrom', form = form)

@app.route('/problem', methods=['GET', 'POST'])
def problem():
    post=[]
    page = request.args.get('page', 1, type=int)
    posts = Problem.query.paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('problem', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('problem', page=posts.prev_num) \
        if posts.has_prev else None
    problem = posts.items
    for p in problem:
        tmp = {}
        tmp['id'] = str(p.id)
        tmp['title'] = p.title
        tmp['source'] = p.source
        records = Record.query.filter_by(problem_id=p.id).all()
        record = Record.query.filter_by(problem_id=p.id,answer='accept').all()
        if len(records)!=0:
            tmp['radio'] = str(int(10000.0*len(record)/len(records))*1.0/100)+"%("+str(len(record))+"/"+str(len(records))+")"
        else :
            tmp['radio'] = "0.00%(0/0)"
        post.append(tmp)
    return render_template('problem.html', title='Problem', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@login_required
@app.route('/commit/<id>', methods=['GET', 'POST'])
def commit(id):
    problem=Problem.query.filter_by(id=id).first_or_404()
    posts={}
    posts['id'] = str(id)
    posts['title'] = problem.title
    form = Commit()
    if form.validate_on_submit():
        record = Record(language = form.language.data, code = form.code.data, user_id = current_user.id, problem_id = id)
        record.timesubmit = datetime.utcnow()
        record.answer = "Pending"
        record.ms = 0
        record.kb = 0
        db.session.add(record)
        db.session.commit()
        flash('Your submission have been commited.')
        return redirect(url_for('status'))
    return render_template('commit.html', title='Commit', posts=posts, form = form)

@login_required
@app.route('/status')
def status():
    post=[]
    page = request.args.get('page', 1, type=int)
    posts = Record.query.order_by(-Record.id).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('status', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('status', page=posts.prev_num) \
        if posts.has_prev else None
    record = posts.items
    for p in record:
        tmp = {}
        tmp['id'] = str(p.id)
        s = str(p.timesubmit)
        tmp['time'] = s[:-7]
        tmp['language'] = p.language
        tmp['problemid'] = p.problem_id
        user = User.query.filter_by(id = p.user_id).first()
        tmp['user'] = user.username
        tmp['status'] = p.answer
        tmp['size'] = len(bytes(p.code, encoding = 'utf8'))
        tmp['ms'] = p.ms
        tmp['kb'] = p.kb
        post.append(tmp)
    return render_template('status.html', title='Status',  posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@login_required
@app.route('/addproblem', methods=['GET', 'POST'])
def addproblem():
    form = AddProblem()
    if form.validate_on_submit():
        problem = Problem(title = form.title.data, content = form.content.data, source = form.source.data, hint = form.source.data, ms = form.ms.data, kb = form.kb.data)
        db.session.add(problem)
        db.session.commit()
        flash('Your changes have been saved.')
    return render_template('addproblem.html', title='Add Problem', form=form)

@app.route('/upload',methods=['POST'])
@login_required
def upload():
    file=request.files.get('editormd-image-file')
    if not file:
        res={
            'success':0,
            'message':'上传失败'
        }
    else:
        ex=os.path.splitext(file.filename)[1]
        filename=datetime.now().strftime('%Y%m%d%H%M%S')+ex
        file.save("image/"+filename)
        res={
            'success':1,
            'message':'上传成功',
            'url':url_for('image',name=filename)
        }
    return jsonify(res)

@app.route('/image/<name>',methods=['GET'])
@login_required
def image(name):
    with open(os.path.join('./image/',name),'rb') as f:
        resp=Response(f.read(),mimetype="image/jpeg")
    return resp

@app.route('/problem_content/<problemid>')
def problem_content(problemid):
    problem=Problem.query.filter_by(id = problemid).first_or_404()
    posts={}
    posts['id'] = problemid
    posts['title'] = problem.title
    posts['content'] = problem.content
    posts['ms'] = problem.ms
    posts['kb'] = problem.kb
    posts['source'] = problem.source
    posts['hint'] = problem.hint
    posts['key']='Problem '+str(problemid)+' '+problem.title
    return render_template('problem_content.html', title='Problem'+str(problemid), posts=posts)


@app.route('/test1', methods=['GET', 'POST'])
def test1():
    mkd = '''
    # header
    ## header2
    [picture](http://www.example.com)
    * 1
    * 2
    * 3
    **bold**
    '''
    return render_template('test1.html', mkd=mkd)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username = username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, limit=0)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form) 

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))