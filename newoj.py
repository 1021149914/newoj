from app import app, db
from app.models import User, Problem, Contest, Inform, Record

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Problem': Problem, 'Contest': Contest, 'Inform': Inform, 'Record': Record}