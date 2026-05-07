from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import csv, io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SECRET_KEY'] = 'sms_secret_key_v3'
db = SQLAlchemy(app)

class Student(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    roll_no      = db.Column(db.String(20),  unique=True, nullable=False)
    department   = db.Column(db.String(50),  nullable=False)
    num_subjects = db.Column(db.Integer,     nullable=False, default=5)

    sub1_name  = db.Column(db.String(60), default='Python Programming')
    sub1_marks = db.Column(db.Float, default=0)
    sub1_max   = db.Column(db.Float, default=100)

    sub2_name  = db.Column(db.String(60), default='Data Structures')
    sub2_marks = db.Column(db.Float, default=0)
    sub2_max   = db.Column(db.Float, default=100)

    sub3_name  = db.Column(db.String(60), default='DBMS')
    sub3_marks = db.Column(db.Float, default=0)
    sub3_max   = db.Column(db.Float, default=100)

    sub4_name  = db.Column(db.String(60), default='Computer Networks')
    sub4_marks = db.Column(db.Float, default=0)
    sub4_max   = db.Column(db.Float, default=100)

    sub5_name  = db.Column(db.String(60), default='Mathematics')
    sub5_marks = db.Column(db.Float, default=0)
    sub5_max   = db.Column(db.Float, default=100)

    def subjects(self):
        return [
            (self.sub1_name, self.sub1_marks, self.sub1_max),
            (self.sub2_name, self.sub2_marks, self.sub2_max),
            (self.sub3_name, self.sub3_marks, self.sub3_max),
            (self.sub4_name, self.sub4_marks, self.sub4_max),
            (self.sub5_name, self.sub5_marks, self.sub5_max),
        ][:self.num_subjects]

    def total_marks(self):
        return sum(m for _, m, _ in self.subjects())

    def total_max(self):
        return sum(mx for _, _, mx in self.subjects())

    def percentage(self):
        mx = self.total_max()
        return round((self.total_marks() / mx) * 100, 1) if mx else 0

    def grade(self):
        p = self.percentage()
        if p >= 80: return 'A'
        elif p >= 60: return 'B'
        elif p >= 40: return 'C'
        else: return 'F'

    def initials(self):
        parts = self.name.strip().split()
        return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else self.name[:2].upper()

    def sub_pct(self, marks, max_marks):
        return round((marks / max_marks) * 100, 1) if max_marks else 0


@app.route('/')
def dashboard():
    all_s = Student.query.all()
    total = len(all_s)
    avg   = round(sum(s.percentage() for s in all_s) / total, 1) if total else 0
    failing = sum(1 for s in all_s if s.grade() == 'F')
    depts = {}
    for s in all_s:
        depts[s.department] = depts.get(s.department, 0) + 1
    top = sorted(all_s, key=lambda s: s.percentage(), reverse=True)[:5]
    dept_list = [d[0] for d in db.session.query(Student.department).distinct().all()]
    return render_template('dashboard.html', total=total, avg=avg,
                           failing=failing, depts=depts, top=top, dept_list=dept_list)


@app.route('/students')
def students():
    search    = request.args.get('search', '')
    dept      = request.args.get('dept', '')
    query     = Student.query
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) | (Student.roll_no.ilike(f'%{search}%'))
        )
    if dept:
        query = query.filter(Student.department == dept)
    student_list = query.all()
    dept_list = [d[0] for d in db.session.query(Student.department).distinct().all()]
    return render_template('students.html', students=student_list,
                           search=search, dept=dept, dept_list=dept_list,
                           total=Student.query.count())


@app.route('/student/<int:id>')
def student_detail(id):
    return render_template('student_detail.html', student=Student.query.get_or_404(id))


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        f = request.form
        name, roll_no = f['name'].strip(), f['roll_no'].strip()
        if not name or not roll_no:
            flash('Name and Roll Number required.', 'error')
            return redirect(url_for('add_student'))
        if Student.query.filter_by(roll_no=roll_no).first():
            flash('Roll number already exists.', 'error')
            return redirect(url_for('add_student'))

        def gm(k):
            try: return max(0, float(f.get(k, 0)))
            except: return 0

        db.session.add(Student(
            name=name, roll_no=roll_no, department=f['department'],
            num_subjects=int(f.get('num_subjects', 5)),
            sub1_name=f.get('sub1_name','Subject 1'), sub1_marks=gm('sub1_marks'), sub1_max=gm('sub1_max') or 100,
            sub2_name=f.get('sub2_name','Subject 2'), sub2_marks=gm('sub2_marks'), sub2_max=gm('sub2_max') or 100,
            sub3_name=f.get('sub3_name','Subject 3'), sub3_marks=gm('sub3_marks'), sub3_max=gm('sub3_max') or 100,
            sub4_name=f.get('sub4_name','Subject 4'), sub4_marks=gm('sub4_marks'), sub4_max=gm('sub4_max') or 100,
            sub5_name=f.get('sub5_name','Subject 5'), sub5_marks=gm('sub5_marks'), sub5_max=gm('sub5_max') or 100,
        ))
        db.session.commit()
        flash(f'{name} added!', 'success')
        return redirect(url_for('students'))
    return render_template('add_student.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    s = Student.query.get_or_404(id)
    if request.method == 'POST':
        f = request.form
        def gm(k):
            try: return max(0, float(f.get(k, 0)))
            except: return 0
        s.name=f['name'].strip(); s.roll_no=f['roll_no'].strip()
        s.department=f['department']; s.num_subjects=int(f.get('num_subjects',5))
        s.sub1_name=f.get('sub1_name','Subject 1'); s.sub1_marks=gm('sub1_marks'); s.sub1_max=gm('sub1_max') or 100
        s.sub2_name=f.get('sub2_name','Subject 2'); s.sub2_marks=gm('sub2_marks'); s.sub2_max=gm('sub2_max') or 100
        s.sub3_name=f.get('sub3_name','Subject 3'); s.sub3_marks=gm('sub3_marks'); s.sub3_max=gm('sub3_max') or 100
        s.sub4_name=f.get('sub4_name','Subject 4'); s.sub4_marks=gm('sub4_marks'); s.sub4_max=gm('sub4_max') or 100
        s.sub5_name=f.get('sub5_name','Subject 5'); s.sub5_marks=gm('sub5_marks'); s.sub5_max=gm('sub5_max') or 100
        db.session.commit()
        flash(f'{s.name} updated!', 'success')
        return redirect(url_for('student_detail', id=s.id))
    return render_template('edit_student.html', student=s)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    s = Student.query.get_or_404(id)
    name = s.name
    db.session.delete(s); db.session.commit()
    flash(f'{name} deleted.', 'success')
    return redirect(url_for('students'))


@app.route('/import', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('import_csv'))
        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed.', 'error')
            return redirect(url_for('import_csv'))

        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)

        added = 0
        skipped = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            try:
                name     = row.get('name', '').strip()
                roll_no  = row.get('roll_no', '').strip()
                dept     = row.get('department', '').strip()
                num_subs = int(row.get('num_subjects', 5) or 5)

                if not name or not roll_no or not dept:
                    errors.append(f'Row {i}: missing name, roll_no or department. skipped.')
                    skipped += 1
                    continue

                valid_depts = ['Computer Science','Information Technology','Electronics','Mechanical','Civil']
                if dept not in valid_depts:
                    errors.append(f'Row {i} ({name}): invalid department "{dept}". skipped.')
                    skipped += 1
                    continue

                if Student.query.filter_by(roll_no=roll_no).first():
                    errors.append(f'Row {i} ({name}): roll number {roll_no} already exists. skipped.')
                    skipped += 1
                    continue

                def gm(key, default=0):
                    try: return max(0, float(row.get(key, default) or default))
                    except: return default

                student = Student(
                    name=name, roll_no=roll_no, department=dept, num_subjects=num_subs,
                    sub1_name=row.get('sub1_name','Subject 1') or 'Subject 1',
                    sub1_marks=gm('sub1_marks'), sub1_max=gm('sub1_max', 100) or 100,
                    sub2_name=row.get('sub2_name','Subject 2') or 'Subject 2',
                    sub2_marks=gm('sub2_marks'), sub2_max=gm('sub2_max', 100) or 100,
                    sub3_name=row.get('sub3_name','Subject 3') or 'Subject 3',
                    sub3_marks=gm('sub3_marks'), sub3_max=gm('sub3_max', 100) or 100,
                    sub4_name=row.get('sub4_name','Subject 4') or 'Subject 4',
                    sub4_marks=gm('sub4_marks'), sub4_max=gm('sub4_max', 100) or 100,
                    sub5_name=row.get('sub5_name','Subject 5') or 'Subject 5',
                    sub5_marks=gm('sub5_marks'), sub5_max=gm('sub5_max', 100) or 100,
                )
                db.session.add(student)
                added += 1

            except Exception as e:
                errors.append(f'Row {i}: unexpected error — {str(e)}. skipped.')
                skipped += 1

        db.session.commit()

        if added:
            flash(f'{added} student(s) imported successfully!', 'success')
        if skipped:
            flash(f'{skipped} row(s) skipped.', 'error')

        return render_template('import.html', errors=errors, added=added, skipped=skipped, done=True)

    return render_template('import.html', done=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)