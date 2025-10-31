from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import io
from PyPDF2 import PdfReader
from transformers import T5ForConditionalGeneration, T5Tokenizer

app = Flask(__name__)
# Initialize model and tokenizer
model_name = "valhalla/t5-base-qg-hl"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)
app.secret_key = 'dev_secret_key' # Needed for flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Student {self.name}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    teacher = db.relationship('Teacher', backref=db.backref('courses_taught', lazy=True))

    def __repr__(self):
        return f'<Course {self.name}>'

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    # courses_taught is available via backref from Course.teacher

    def __repr__(self):
        return f'<Teacher {self.name}>'

@app.route('/')
def home():
    return render_template('home.html')

# Student Management Routes
@app.route('/students')
def list_students():
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Check if email already exists
        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            # Handle error: email already exists
            # For now, let's just render the form again with a message (not implemented yet)
            # Or simply redirect back to the form or student list.
            # A flash message would be good here.
            return redirect(url_for('add_student')) # Or render_template with error

        new_student = Student(name=name, email=email)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('list_students'))

    return render_template('student_form.html',
                           title='Add Student',
                           action_url=url_for('add_student'),
                           submit_button_text='Add Student',
                           student=None)

@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student_to_edit = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        new_email = request.form['email']
        # Check if the new email is already used by another student
        existing_student_with_new_email = Student.query.filter(Student.id != student_id, Student.email == new_email).first()
        if existing_student_with_new_email:
            # Email already in use by another student, handle error
            # For now, redirect or render with error. Flash message would be good.
            return redirect(url_for('edit_student', student_id=student_id))


        student_to_edit.name = request.form['name']
        student_to_edit.email = new_email
        db.session.commit()
        return redirect(url_for('list_students'))

    return render_template('student_form.html',
                           title='Edit Student',
                           action_url=url_for('edit_student', student_id=student_id),
                           submit_button_text='Save Changes',
                           student=student_to_edit)

@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student_to_delete = Student.query.get_or_404(student_id)
    db.session.delete(student_to_delete)
    db.session.commit()
    return redirect(url_for('list_students'))

# Course Management Routes
@app.route('/courses')
def list_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        teacher_id_str = request.form.get('teacher_id')

        final_teacher_id = None
        if teacher_id_str: # Check if not empty or None
            try:
                final_teacher_id = int(teacher_id_str)
            except ValueError:
                flash('Invalid Teacher ID format.', 'error')
                # Re-fetch teachers for rendering the form again with an error
                teachers = Teacher.query.all()
                return render_template('course_form.html',
                                       title='Add Course',
                                       action_url=url_for('add_course'),
                                       submit_button_text='Add Course',
                                       course={'name': name, 'description': description}, # pass current form data
                                       teachers=teachers,
                                       selected_teacher_id=teacher_id_str) # Pass invalid string to show selection

        new_course = Course(name=name, description=description, teacher_id=final_teacher_id)
        db.session.add(new_course)
        db.session.commit()
        flash(f"Course '{name}' added successfully!", 'success')
        return redirect(url_for('list_courses'))

    teachers = Teacher.query.all()
    return render_template('course_form.html',
                           title='Add Course',
                           action_url=url_for('add_course'),
                           submit_button_text='Add Course',
                           course=None,
                           teachers=teachers)

@app.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course_to_edit = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course_to_edit.name = request.form['name']
        course_to_edit.description = request.form['description']
        teacher_id_str = request.form.get('teacher_id')

        final_teacher_id = None
        if teacher_id_str: # Check if not empty or None
            try:
                final_teacher_id = int(teacher_id_str)
            except ValueError:
                flash('Invalid Teacher ID format.', 'error')
                # Re-fetch teachers for rendering the form again with an error
                teachers = Teacher.query.all()
                # Pass back current form data, including the problematic teacher_id string
                # The course object for the form should reflect what the user was trying to save
                current_form_data = {
                    'id': course_id, # needed for action_url
                    'name': course_to_edit.name,
                    'description': course_to_edit.description,
                    # For teacher_id, we'd ideally show the selection that caused error
                    # but course.teacher_id expects an int. So, we'll manage selected_teacher_id in template
                }
                return render_template('course_form.html',
                                       title='Edit Course',
                                       action_url=url_for('edit_course', course_id=course_id),
                                       submit_button_text='Save Changes',
                                       course=course_to_edit, # pass original course to prefill if needed
                                       teachers=teachers,
                                       # Add a way to show the attempted selection if it was invalid
                                       # For simplicity, we might just let it default or clear
                                      )

        course_to_edit.teacher_id = final_teacher_id
        db.session.commit()
        flash(f"Course '{course_to_edit.name}' updated successfully!", 'success')
        return redirect(url_for('list_courses'))

    teachers = Teacher.query.all()
    return render_template('course_form.html',
                           title='Edit Course',
                           action_url=url_for('edit_course', course_id=course_id),
                           submit_button_text='Save Changes',
                           course=course_to_edit,
                           teachers=teachers)

@app.route('/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course_to_delete = Course.query.get_or_404(course_id)
    db.session.delete(course_to_delete)
    db.session.commit()
    return redirect(url_for('list_courses'))

# Teacher Management Routes
@app.route('/teachers')
def list_teachers():
    teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        existing_teacher = Teacher.query.filter_by(email=email).first()
        if existing_teacher:
            flash(f"Teacher with email '{email}' already exists.", 'error')
            return render_template('teacher_form.html',
                                   title='Add Teacher',
                                   action_url=url_for('add_teacher'),
                                   submit_button_text='Add Teacher',
                                   teacher={'name': name, 'email': email}) # Pass back current form data

        new_teacher = Teacher(name=name, email=email)
        db.session.add(new_teacher)
        db.session.commit()
        flash(f"Teacher '{name}' added successfully!", 'success')
        return redirect(url_for('list_teachers'))

    return render_template('teacher_form.html',
                           title='Add Teacher',
                           action_url=url_for('add_teacher'),
                           submit_button_text='Add Teacher',
                           teacher=None)

@app.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher_to_edit = Teacher.query.get_or_404(teacher_id)

    if request.method == 'POST':
        new_name = request.form['name']
        new_email = request.form['email']

        # Check if the new email is already used by another teacher
        existing_teacher = Teacher.query.filter(Teacher.id != teacher_id, Teacher.email == new_email).first()
        if existing_teacher:
            flash(f"Another teacher with email '{new_email}' already exists.", 'error')
            return render_template('teacher_form.html',
                                   title='Edit Teacher',
                                   action_url=url_for('edit_teacher', teacher_id=teacher_id),
                                   submit_button_text='Save Changes',
                                   teacher={'id': teacher_id, 'name': new_name, 'email': new_email})


        teacher_to_edit.name = new_name
        teacher_to_edit.email = new_email
        db.session.commit()
        flash(f"Teacher '{teacher_to_edit.name}' updated successfully!", 'success')
        return redirect(url_for('list_teachers'))

    return render_template('teacher_form.html',
                           title='Edit Teacher',
                           action_url=url_for('edit_teacher', teacher_id=teacher_id),
                           submit_button_text='Save Changes',
                           teacher=teacher_to_edit)

@app.route('/teachers/delete/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    teacher_to_delete = Teacher.query.get_or_404(teacher_id)
    try:
        db.session.delete(teacher_to_delete)
        db.session.commit()
        flash(f"Teacher '{teacher_to_delete.name}' deleted successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting teacher '{teacher_to_delete.name}': {str(e)}", 'error')
        # Potentially, if there are related courses that prevent deletion due to foreign key constraints (once added)
        # For now, this generic error handling is a placeholder.
    return redirect(url_for('list_teachers'))

# PDF Question Generation Route
@app.route('/soru-uret', methods=['GET', 'POST'])
def soru_uret():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['pdf_file']

        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            try:
                pdf_stream = io.BytesIO(file.read())
                reader = PdfReader(pdf_stream)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""

                if not text.strip():
                    flash('Could not extract text from PDF.', 'error')
                    return render_template('soru_uret.html', questions=None)

                question_count = int(request.form.get('question_count', 5))

                # Preprocess text for the model
                input_text = "generate questions: " + text
                input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

                # Generate questions
                outputs = model.generate(
                    input_ids,
                    max_length=64,
                    num_beams=4,
                    early_stopping=True,
                    num_return_sequences=question_count
                )

                questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

                return render_template('soru_uret.html', questions=questions)

            except Exception as e:
                flash(f'An error occurred: {e}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a PDF.', 'error')
            return redirect(request.url)

    return render_template('soru_uret.html', questions=None)

if __name__ == '__main__':
    app.run(debug=True)
