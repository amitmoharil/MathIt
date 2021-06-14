from flask import render_template, Flask, request, session, redirect
import random
from flask.helpers import url_for 
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "SomeSecretKey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mathgame.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)

operators = ['+','-','*']

class MathGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    date = db.Column(db.DateTime, unique=False,  nullable=False, default=datetime.utcnow)
    score = db.Column(db.Integer, unique=False, nullable=False)
    digits = db.Column(db.Integer, unique=False, nullable=False)
    duration = db.Column(db.Integer, unique=False, nullable=False)

@app.route('/')
def index():
    if session.get("valid", False):
        if session.get("complete", False):
            name = session["name"]
            digits = session["digits"]
            time = session["time"]
            print(digits, time)
            return render_template('index.html', name=name, digits=digits, time=time)
        else:
            return redirect('result')
    else:
        return render_template('index.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/enter', methods=["POST"])
def enter():
    session.clear()
    session["digits"] = int(request.form['digits'])
    session["time"] = int(request.form["time"])
    session["name"] = request.form["name"]
    session["valid"] = True
    session["total"] = 0
    session["correct"] = 0
    session["complete"] = False
    session["answered"] = 0
    return redirect(url_for('start', question=1))

@app.route('/questions/<int:question>', methods=['GET', 'POST'])
def start(question, scoring=None):
    if session["complete"]:
        return redirect(url_for('index'))
        
    if session["valid"]:
        if session.get(f"question{question}", 0) == 0:
            digits = session["digits"]
            op1 = random.randint(int(10**(digits-1)), int(10**digits)-1)
            op2 = random.randint(int(10**(digits-1)), int(10**digits)-1)
            operator = operators[random.randint(0,2)]
            session[f"question{question}"] = (op1, operator, op2)
            session["total"] += 1
            session[f"result{question}"] = eval(str(op1)+operator+str(op2))
           
        op1, operator, op2 = session[f"question{question}"]        
        correct = session["correct"]
        total = session["total"]
        answered = session["answered"]
        return render_template('question.html', op1=op1, op2=op2, operator=operator, question=question, correct=correct, total=total, answered=answered)
    else:
        return redirect(url_for('index'))

@app.route('/evaluate/<int:question>', methods=["POST"])
def evaluate(question):
    session[f"answer{question}"] = request.form["answer"]
    if eval(request.form["answer"]) == session[f"result{question}"]:
        session["correct"] += 1

    session["answered"] += 1
    return redirect(url_for('start',question=question+1))

@app.route('/result')
def result():
    if not session["complete"]:
        new_math_game = MathGame(name=session["name"], score=session["correct"], duration=session["time"], digits=session["digits"])
        db.session.add(new_math_game)
        db.session.commit()
        session["id"] = new_math_game.id
        session["complete"] = True
        print('Here')
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Sept', 'Oct', 'Nov', 'Dec']
    all_games = MathGame.query.order_by(MathGame.score.desc()).all()
    ranks = [1]
    my_rank = 0
    if all_games[0].id == session["id"]:
        my_rank = 1 
        
    for i in range(1, len(all_games)):
        if all_games[i].score == all_games[i-1].score:
            ranks.append(ranks[i-1])
        else:
            ranks.append(ranks[i-1]+1)

        if all_games[i].id == session["id"]:
            my_rank = ranks[i]
            if i>10:
                break


    print(session["id"], my_rank)
    leaderboard = all_games[:10]
    i = 10
    while i<len(all_games) and all_games[i].score == all_games[i-1].score:
        if i>=len(ranks):
            ranks.append(ranks[i-1])
        leaderboard.append(all_games[i])
        i+=1 
    print(ranks)
    return render_template('result.html', leaderboard=leaderboard, months=months, rank=my_rank, ranks=ranks, id=session["id"])

if __name__ == '__main__':
    app.run(debug=True)