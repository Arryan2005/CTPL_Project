from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SECRET_KEY'] = 'sms_secret_key'
db = SQLAlchemy(app)

CS_SUBJECTS = [
    'Python Programming',
    'Data Structures',
    'DBMS',
    'Computer Networks',
    'Mathematics'
]

class Student(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    roll_no    = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)

    marks_python  = db.Column(db.Float, nullable=False, default=0)
    marks_ds      = db.Column(db.Float, nullable=False, default=0)
    marks_dbms    = db.Column(db.Float, nullable=False, default=0)
    marks_cn      = db.Column(db.Float, nullable=False, default=0)
    marks_maths   = db.Column(db.Float, nullable=False, default=0)

    max_python    = db.Column(db.Float, nullable=False, default=100)
    max_ds        = db.Column(db.Float, nullable=False, default=100)
    max_dbms      = db.Column(db.Float, nullable=False, default=100)
    max_cn        = db.Column(db.Float, nullable=False, default=100)
    max_maths     = db.Column(db.Float, nullable=False, default=100)

    def total_obtained(self):
        return self.marks_python + self.marks_ds + self.marks_dbms + self.marks_cn + self.marks_maths

    def total_max(self):
        return self.max_python + self.max_ds + self.max_dbms + self.max_cn + self.max_maths

    def percentage(self):
        if self.total_max() == 0:
            return 0
        return round((self.total_obtained() / self.total_max()) * 100, 1)

    def grade(self):
        p = self.percentage()
        if p >= 80:   return 'A'
        elif p >= 60: return 'B'
        elif p >= 40: return 'C'
        else:         return 'F'

    def subject_marks(self):
        return [
            {'name': 'Python Programming', 'obtained': self.marks_python, 'max': self.max_python},
            {'name': 'Data Structures',    'obtained': self.marks_ds,     'max': self.max_ds},
            {'name': 'DBMS',               'obtained': self.marks_dbms,   'max': self.max_dbms},
            {'name': 'Computer Networks',  'obtained': self.marks_cn,     'max': self.max_cn},
            {'name': 'Mathematics',        'obtained': self.marks_maths,  'max': self.max_maths},
        ]

@app.route('/')
def index():
    search   = request.args.get('search', '')
    query    = Student.query
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Student.roll_no.ilike(f'%{search}%'))
        )
    students = query.all()
    total    = Student.query.count()
    all_s    = Student.query.all()
    avg_pct  = round(sum(s.percentage() for s in all_s) / total, 1) if total else 0
    failing  = sum(1 for s in all_s if s.grade() == 'F')
    return render_template('index.html', students=students, total=total,
                           avg_pct=avg_pct, failing=failing, search=search)

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name    = request.form['name'].strip()
        roll_no = request.form['roll_no'].strip()

        if not name or not roll_no:
            flash('Name and roll number are required.', 'error')
            return redirect(url_for('add_student'))

        if Student.query.filter_by(roll_no=roll_no).first():
            flash('Roll number already exists.', 'error')
            return redirect(url_for('add_student'))

        keys = ['python', 'ds', 'dbms', 'cn', 'maths']
        obtained = {}
        maxmarks = {}
        for k in keys:
            try:
                o = float(request.form[f'marks_{k}'])
                m = float(request.form[f'max_{k}'])
                if o < 0 or m <= 0 or o > m:
                    raise ValueError
                obtained[k] = o
                maxmarks[k] = m
            except (ValueError, KeyError):
                flash('Invalid marks. Check obtained and max values.', 'error')
                return redirect(url_for('add_student'))

        student = Student(
            name=name, roll_no=roll_no, department='Computer Science',
            marks_python=obtained['python'], marks_ds=obtained['ds'],
            marks_dbms=obtained['dbms'],     marks_cn=obtained['cn'],
            marks_maths=obtained['maths'],
            max_python=maxmarks['python'],   max_ds=maxmarks['ds'],
            max_dbms=maxmarks['dbms'],       max_cn=maxmarks['cn'],
            max_maths=maxmarks['maths'],
        )
        db.session.add(student)
        db.session.commit()
        flash(f'{name} added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_student.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name    = request.form['name'].strip()
        student.roll_no = request.form['roll_no'].strip()
        keys = ['python', 'ds', 'dbms', 'cn', 'maths']
        for k in keys:
            try:
                o = float(request.form[f'marks_{k}'])
                m = float(request.form[f'max_{k}'])
                if o < 0 or m <= 0 or o > m:
                    raise ValueError
                setattr(student, f'marks_{k}', o)
                setattr(student, f'max_{k}', m)
            except (ValueError, KeyError):
                flash('Invalid marks for one of the subjects.', 'error')
                return redirect(url_for('edit_student', id=id))
        db.session.commit()
        flash(f'{student.name} updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_student.html', student=student)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f'{name} deleted.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)