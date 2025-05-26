from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

# In-memory database for students
students_db = []
next_student_id = 1

# In-memory database for courses
# Course structure: {'id': int, 'name': str, 'description': str, 'teacher_id': int/str/None}
courses_db = []
next_course_id = 1

@app.route('/')
def home():
    return render_template('home.html')

# Route to list students
@app.route('/students')
def list_students():
    return render_template('students.html', students=students_db)

# Route to add a new student
@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    global next_student_id
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        new_student = {
            'id': next_student_id,
            'name': name,
            'email': email
        }
        students_db.append(new_student)
        next_student_id += 1
        return redirect(url_for('list_students'))
    
    # For GET request, show the form
    return render_template('student_form.html', 
                           title='Add Student', 
                           action_url=url_for('add_student'), 
                           submit_button_text='Add Student', 
                           student=None)

# Route to edit an existing student
@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student_to_edit = None
    for student in students_db:
        if student['id'] == student_id:
            student_to_edit = student
            break
    
    if student_to_edit is None:
        abort(404) # Or return a custom error page

    if request.method == 'POST':
        student_to_edit['name'] = request.form['name']
        student_to_edit['email'] = request.form['email']
        return redirect(url_for('list_students'))
    
    # For GET request, show the form with student's data
    return render_template('student_form.html', 
                           title='Edit Student', 
                           action_url=url_for('edit_student', student_id=student_id), 
                           submit_button_text='Save Changes', 
                           student=student_to_edit)

# Route to delete a student
@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    global students_db
    student_to_delete = None
    for student in students_db:
        if student['id'] == student_id:
            student_to_delete = student
            break
            
    if student_to_delete:
        students_db.remove(student_to_delete)
    else:
        # Optionally, handle the case where the student is not found, 
        # though the form structure should prevent this.
        abort(404) 
        
    return redirect(url_for('list_students'))

# Course Management Routes

# Route to list courses
@app.route('/courses')
def list_courses():
    return render_template('courses.html', courses=courses_db)

# Route to add a new course
@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    global next_course_id
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        teacher_id = request.form.get('teacher_id') # Use .get for optional field
        
        new_course = {
            'id': next_course_id,
            'name': name,
            'description': description,
            'teacher_id': teacher_id if teacher_id else None # Store as None if empty
        }
        courses_db.append(new_course)
        next_course_id += 1
        return redirect(url_for('list_courses'))
    
    return render_template('course_form.html', 
                           title='Add Course', 
                           action_url=url_for('add_course'), 
                           submit_button_text='Add Course', 
                           course=None)

# Route to edit an existing course
@app.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course_to_edit = None
    for course in courses_db:
        if course['id'] == course_id:
            course_to_edit = course
            break
    
    if course_to_edit is None:
        abort(404)

    if request.method == 'POST':
        course_to_edit['name'] = request.form['name']
        course_to_edit['description'] = request.form['description']
        course_to_edit['teacher_id'] = request.form.get('teacher_id') if request.form.get('teacher_id') else None
        return redirect(url_for('list_courses'))
    
    return render_template('course_form.html', 
                           title='Edit Course', 
                           action_url=url_for('edit_course', course_id=course_id), 
                           submit_button_text='Save Changes', 
                           course=course_to_edit)

# Route to delete a course
@app.route('/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    global courses_db
    course_to_delete = None
    for course in courses_db:
        if course['id'] == course_id:
            course_to_delete = course
            break
            
    if course_to_delete:
        courses_db.remove(course_to_delete)
    else:
        abort(404)
        
    return redirect(url_for('list_courses'))

if __name__ == '__main__':
    app.run(debug=True)
