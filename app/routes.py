from flask import render_template, flash, redirect, url_for, request, jsonify, Response
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddProblem, Commit, AddInform, AddContest, Update
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Problem, Contest, Inform, Record, Contest_Problem
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from sqlalchemy import desc, distinct
from flask_paginate import Pagination, get_page_parameter
from werkzeug import secure_filename
from multiprocessing import Process
import os, json, lorun

RESULT_STR = [
    'Accepted',
    'Presentation Error',
    'Time Limit Exceeded',
    'Memory Limit Exceeded',
    'Wrong Answer',
    'Runtime Error',
    'Output Limit Exceeded',
    'Compile Error',
    'System Error'
]

def compileSrc(src_path,key):
    op = 'g++ %s -o '%src_path
    if os.system(op+key) != 0:
        #print('compile failure!')
        return False
    return True

def compileSrcc(src_path,key):
    op = 'gcc %s -o '%src_path
    if os.system(op+key) != 0:
        #print('compile failure!')
        return False
    return True

def runone(p_path, in_path, out_path,tl,ml,kid):
    fin = open(in_path)
    pa = str(kid)+'.out'
    ftemp = open(pa, 'w')
    
    runcfg = {
        'args':[p_path],
        'fd_in':fin.fileno(),
        'fd_out':ftemp.fileno(),
        'timelimit':eval(tl), #in MS
        'memorylimit':eval(ml), #in KB
        'java': False
    }
    
    rst = lorun.run(runcfg)
    fin.close()
    ftemp.close()
    
    if rst['result'] == 0:
        ftemp = open(pa)
        fout = open(out_path)
        crst = lorun.check(fout.fileno(), ftemp.fileno())
        fout.close()
        ftemp.close()
        os.remove(pa)
        #print(crst)
        if crst != 0:
            return {'result':crst}
    return rst

def judgecp(src_path, td_path, td_total,id,tl,ml,kid):
    record = Record.query.filter_by(id = kid).first_or_404()
    record.answer = "Judging"
    db.session.commit()
    if not compileSrc(src_path,'./'+str(id)):
        return
    for i in range(td_total):
        in_path = os.path.join(td_path, '%d.in'%eval(id))
        out_path = os.path.join(td_path, '%d.out'%eval(id))
        if os.path.isfile(in_path) and os.path.isfile(out_path):
            #print("now rst")
            rst = runone('./'+str(id), in_path, out_path,tl,ml,kid)
            rst['result'] = RESULT_STR[rst['result']]
            #print(rst)
            record.answer = rst['result']
            if "memoryused" in rst.keys():
                record.kb = rst['memoryused']
            if "timeused" in rst.keys():
                record.ms = rst['timeused']
            db.session.commit()
        else:
            #print('testdata:%d incompleted' % i)
            #os.remove('./'+str(id))
            record.answer = "System Error"
            db.session.commit()
            #exit(-1)
    os.remove('./'+str(id))

def judgec(src_path, td_path, td_total,id,tl,ml,kid):
    record = Record.query.filter_by(id = kid).first_or_404()
    record.answer = "Judging"
    db.session.commit()
    if not compileSrcc(src_path,'./'+str(id)):
        return
    for i in range(td_total):
        in_path = os.path.join(td_path, '%d.in'%eval(id))
        out_path = os.path.join(td_path, '%d.out'%eval(id))
        if os.path.isfile(in_path) and os.path.isfile(out_path):
            #print("now rst")
            rst = runone('./'+str(id), in_path, out_path,tl,ml,kid)
            rst['result'] = RESULT_STR[rst['result']]
            #print(rst)
            record.answer = rst['result']
            if "memoryused" in rst.keys():
                record.kb = rst['memoryused']
            if "timeused" in rst.keys():
                record.ms = rst['timeused']
            db.session.commit()
        else:
            #print('testdata:%d incompleted' % i)
            #os.remove('./'+str(id))
            record.answer = "System Error"
            db.session.commit()
            #exit(-1)
    os.remove('./'+str(id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@app.route('/index')
@login_required
def index():
    post=[]
    page = request.args.get('page', 1, type=int)
    if current_user.limit == "0":
        posts = Inform.query.filter_by(limit = "1").paginate(page, app.config['POSTS_PER_PAGE'], False)
    else :
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
    if current_user.limit == "0" :
        posts = Contest.query.filter_by(limit = "1").paginate(page, app.config['POSTS_PER_PAGE'], False)
    else :
        posts = Contest.query.paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('contest', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('contest', page=posts.prev_num) \
        if posts.has_prev else None
    tk = posts.items
    for p in tk:
        tmp = {}
        tmp['id'] = p.id
        tmp['title'] = p.title
        tmp['content'] = p.content
        tmp['source'] = p.source
        tmp['limit'] = p.limit
        t = p.beg_time + timedelta(hours=8)
        tmp['beg_time'] = t
        t = p.end_time + timedelta(hours=8)
        tmp['end_time'] = t
        tmp['pid'] = p.id
        if datetime.now()<p.beg_time :
            tmp['pid'] = 0
        post.append(tmp)
    return render_template('contest.html', title='Contest', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@login_required
@app.route('/edit_contest/<id>', methods=['GET', 'POST'])
def edit_contest(id):
    contest = Contest.query.filter_by(id = id).first_or_404()
    form = AddContest()
    if form.validate_on_submit():
        contest.title = form.title.data
        contest.content = form.content.data
        contest.source = form.source.data
        t = form.beg_time.data
        utct = datetime.utcfromtimestamp(t.timestamp())
        contest.beg_time = utct
        t = form.end_time.data
        utct = datetime.utcfromtimestamp(t.timestamp())
        contest.end_time = utct
        db.session.commit()
        flash('The changes on the contest have been saved.')
        return redirect(url_for('contest'))
    elif request.method == 'GET':
        form.title.data = contest.title
        form.content.data = contest.content
        form.source.data = contest.source
        t = contest.beg_time + timedelta(hours=8)
        form.beg_time.data = t
        t = contest.end_time + timedelta(hours=8)
        form.end_time.data = t
        return render_template('edit_contest.html', title='Edit Contest', form=form)

@login_required
@app.route('/del_contest/<id>', methods=['GET', 'POST'])
def del_contest(id):
    contest = Contest.query.filter_by(id = id).first_or_404()
    db.session.delete(contest)
    db.session.commit()
    flash('The contest have been deleted.')
    return redirect(url_for('contest'))

@login_required
@app.route('/wait', methods=['GET', 'POST'])
def wait():
    return render_template('wait.html', title='Waiting')

@app.route('/contest_problem/<id>', methods=['GET', 'POST'])
def contest_problem(id):
    if id == 0 :
        return redirect(url_for('wait'))
    contest = Contest.query.filter_by(id = id).first_or_404()
    if datetime.utcnow() < contest.beg_time :
        return redirect(url_for('wait'))
    post = []
    posts = Contest_Problem.query.filter_by(contest_id = id).all()
    for p in posts :
        tmp = {}
        tmp['id'] = p.problem_id
        problem = Problem.query.filter_by(id = p.problem_id).first_or_404()
        if problem:
            tmp['title'] = problem.title
            tmp['source'] = problem.source
            post.append(tmp)
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
        contest = Contest(title = form.title.data, source = form.source.data, content = form.content.data, limit = 0)
        t = form.beg_time.data
        utct = datetime.utcfromtimestamp(t.timestamp())
        #print(datetime.fromtimestamp(t.timestamp()))
        contest.beg_time = utct
        t = form.end_time.data
        utct = datetime.utcfromtimestamp(t.timestamp())
        contest.end_time = utct
        db.session.add(contest)
        db.session.commit()
        flash('Your contest have been added. Please add problem.')
        return redirect(url_for('addcontestproblem', id=contest.id))
    elif request.method == 'GET':
        now = datetime.now()
        form.beg_time.data = now
        form.end_time.data = now
        return render_template('addcontest.html', title='Add Contest', form = form)

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
    post=[]
    page = request.args.get('page', 1, type=int)
    posts = User.query.order_by(-User.ac).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('rank', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('rank', page=posts.prev_num) \
        if posts.has_prev else None
    user = posts.items
    for u in user:
        tmp = {}
        tmp['id'] = u.id
        tmp['name'] = u.username
        records = Record.query.filter_by(user_id=u.id).all()
        record = Record.query.filter_by(user_id=u.id,answer='accept').distinct(Record.problem_id).all()
        if len(records)!=0:
            tmp['radio'] = str(int(10000.0*len(record)/len(records))*1.0/100)+"%"
        else :
            tmp['radio'] = "0.00%"
        tmp['ac'] = len(record)
        tmp['total'] = len(records)
        post.append(tmp)
    return render_template('rank.html', title='Rank', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)
    

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
        inform = Inform(title = form.title.data, source = form.source.data, content = form.content.data, limit = 0)
        db.session.add(inform)
        db.session.commit()
        flash('Your announcement have been commited.')
        return redirect(url_for('index'))
    return render_template('addinform.html', title='Add Infrom', form = form)

@login_required
@app.route('/ok_inform/<id>', methods=['GET', 'POST'])
def ok_inform(id):
    inform = Inform.query.filter_by(id = id).first_or_404()
    inform.limit = "1"
    db.session.commit()
    return redirect(url_for('index'))

@login_required
@app.route('/re_inform/<id>', methods=['GET', 'POST'])
def re_inform(id):
    inform = Inform.query.filter_by(id = id).first_or_404()
    inform.limit = "0"
    db.session.commit()
    return redirect(url_for('index'))

@login_required
@app.route('/ok_contest/<id>', methods=['GET', 'POST'])
def ok_contest(id):
    contest = Contest.query.filter_by(id = id).first_or_404()
    contest.limit = "1"
    db.session.commit()
    return redirect(url_for('contest'))

@login_required
@app.route('/re_contest/<id>', methods=['GET', 'POST'])
def re_contest(id):
    contest = Contest.query.filter_by(id = id).first_or_404()
    contest.limit = "0"
    db.session.commit()
    return redirect(url_for('contest'))

@login_required
@app.route('/ok_problem/<id>', methods=['GET', 'POST'])
def ok_problem(id):
    problem = Problem.query.filter_by(id = id).first_or_404()
    problem.limit = "1"
    db.session.commit()
    return redirect(url_for('problem'))

@login_required
@app.route('/re_problem/<id>', methods=['GET', 'POST'])
def re_problem(id):
    problem = Problem.query.filter_by(id = id).first_or_404()
    problem.limit = "0"
    db.session.commit()
    return redirect(url_for('problem'))

@login_required
@app.route('/edit_inform/<id>', methods=['GET','POST'])
def edit_inform(id):
    inform = Inform.query.filter_by(id = id).first_or_404()
    form = AddInform()
    if form.validate_on_submit():
        inform.title = form.title.data
        inform.content = form.content.data
        inform.source = form.source.data
        db.session.commit()
        flash('The changes on the inform have been saved.')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.title.data = inform.title
        form.source.data = inform.source
        return render_template('edit_inform.html', title='Edit Inform', form=form, content = inform.content)

@login_required
@app.route('/del_inform/<id>', methods=['GET','POST'])
def del_inform(id):
    inform = Inform.query.filter_by(id = id).first_or_404()
    db.session.delete(inform)
    db.session.commit()
    flash('The inform have been deleted.')
    return redirect(url_for('index'))

@app.route('/problem', methods=['GET', 'POST'])
def problem():
    post=[]
    page = request.args.get('page', 1, type=int)
    if current_user.limit == "0":
        posts = Problem.query.filter_by(limit = "1").paginate(page, app.config['POSTS_PER_PAGE'], False)
    else :
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
        tmp['limit'] = p.limit
        records = Record.query.filter_by(problem_id=p.id).all()
        record = Record.query.filter_by(problem_id=p.id,answer='accept').all()
        if len(records)!=0:
            tmp['radio'] = str(int(10000.0*len(record)/len(records))*1.0/100)+"%("+str(len(record))+"/"+str(len(records))+")"
        else :
            tmp['radio'] = "0.00%(0/0)"
        post.append(tmp)
    return render_template('problem.html', title='Problem', posts = post, next_url = next_url, prev_url = prev_url, pagination = posts)

@login_required
@app.route('/edit_problem/<id>', methods=['GET', 'POST'])
def edit_problem(id):
    problem = Problem.query.filter_by(id = id).first_or_404()
    form = AddProblem()
    if form.validate_on_submit():
        problem.title = form.title.data
        problem.ms = form.ms.data
        problem.kb = form.kb.data
        problem.content = form.content.data
        problem.source = form.source.data
        problem.hint = form.hint.data
        db.session.commit()
        flash('The changes on the problem have been saved.')
        return redirect(url_for('problem'))
    elif request.method == 'GET':
        form.title.data = problem.title
        form.ms.data = problem.ms
        form.kb.data = problem.kb
        form.source.data = problem.source
        form.hint.data = problem.hint
        return render_template('edit_problem.html', title='Edit Problem', form=form, content = problem.content)

@login_required
@app.route('/del_problem/<id>', methods=['GET', 'POST'])
def del_problem(id):
    problem = Problem.query.filter_by(id = id).first_or_404()
    db.session.delete(problem)
    db.session.commit()
    flash('The problem have been deleted.')
    return redirect(url_for('problem'))

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
        if record.language == "C++" :
            with open('./commit/'+str(record.id)+'.cpp',"w") as f:
                f.write(record.code)
            #print("here c++ run")
            p = Process(target=judgecp,args =('./commit/'+str(record.id)+'.cpp','./data',1,id,problem.ms,problem.kb,record.id))
            #print("p is ok")
            p.start()
            #print("p is start")
        elif record.language == "C" :
            with open('./commit/'+str(record.id)+'.c',"w") as f:
                f.write(record.code)
            p = Process(target=judgec,args =('./commit/'+str(record.id)+'.c','./data',1,id,problem.ms,problem.kb,record.id))
            p.start()
        record = Record.query.filter_by(problem_id=id,answer='accept',user_id=current_user.id).all()
        if len(record)==1:
            user = User.query.filter_by(id= current_user.id).first_or_404()
            user.ac =user.ac +1
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
        problem = Problem(title = form.title.data, content = form.content.data, source = form.source.data, hint = form.hint.data, ms = form.ms.data, kb = form.kb.data, limit =0)
        db.session.add(problem)
        db.session.commit()
        flash('The problem have been saved.')
        return redirect(url_for('update', id = problem.id))
    return render_template('addproblem.html', title='Add Problem', form=form)

@login_required
@app.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    if request.method == 'POST':
        stdin = request.files['stdin']
        stdout = request.files['stdout']
        stdin.save('./data/'+str(id)+'.in')
        stdout.save('./data/'+str(id)+'.out')
        flash('The problem have been saved.')
        return redirect(url_for('index'))
    else :
        problem = Problem.query.filter_by(id = id).first_or_404()
        return render_template('update.html', title='Update', problem = problem)

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

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username = username).first_or_404()
    posts = {}
    records = Record.query.filter_by(user_id=user.id).all()
    record = Record.query.filter_by(user_id=user.id,answer='accept').distinct(Record.problem_id).all()
    posts['ac'] = len(record)
    posts['total'] = len(records)
    t = current_user.last_seen + timedelta(hours=8)
    t = str(t)
    posts['time'] = t[:-7]
    return render_template('user.html', title = username, user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user',username = current_user.username))
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
        user.ac = 0
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
