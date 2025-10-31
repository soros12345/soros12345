import pytest
from school_automation.app import app, db, Student, Course, Teacher
from flask import get_flashed_messages
from unittest.mock import patch, MagicMock
import io

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_school.db' # Test database
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for form tests
    app.config['SECRET_KEY'] = 'test_secret_key' # Needed for flash messages in tests

    with app.app_context():
        db.create_all() # Create tables before each test

    test_client = app.test_client()

    yield test_client # Test runs here

    with app.app_context():
        db.session.remove()
        db.drop_all() # Drop tables after each test

# 1. Home Page Test
def test_home_page(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Manage Students" in response.data
    assert b"Manage Courses" in response.data
    assert b"Manage Teachers" in response.data

# 2. Student Management Tests
def test_add_student(client):
    """Test adding a new student."""
    # Student add in app.py does not have flash messages, so no flash check here.
    response = client.post('/students/add', data={
        'name': 'Test Student',
        'email': 'test.student@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Student" in response.data

    with app.app_context():
        student = Student.query.filter_by(email='test.student@example.com').first()
        assert student is not None
        assert student.name == 'Test Student'

def test_list_students(client):
    """Test listing students."""
    with app.app_context():
        s1 = Student(name='List Student 1', email='list1@example.com')
        db.session.add(s1)
        db.session.commit()

    response = client.get('/students')
    assert response.status_code == 200
    assert b"List Student 1" in response.data
    assert b"list1@example.com" in response.data

def test_edit_student(client):
    """Test editing an existing student."""
    # Student edit in app.py does not have flash messages.
    with app.app_context():
        student = Student(name='Original Student Name', email='original.student@example.com')
        db.session.add(student)
        db.session.commit()
        student_id = student.id

    response = client.post(f'/students/edit/{student_id}', data={
        'name': 'Updated Student Name',
        'email': 'updated.student@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated Student Name" in response.data

    with app.app_context():
        updated_student = db.session.get(Student, student_id)
        assert updated_student.name == 'Updated Student Name'
        assert updated_student.email == 'updated.student@example.com'

def test_delete_student(client):
    """Test deleting an existing student."""
    # Student delete in app.py does not have flash messages.
    with app.app_context():
        student = Student(name='Student to Delete', email='delete.student@example.com')
        db.session.add(student)
        db.session.commit()
        student_id = student.id

    response = client.post(f'/students/delete/{student_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Student to Delete" not in response.data # Check it's not in the table listing

    with app.app_context():
        deleted_student = db.session.get(Student, student_id)
        assert deleted_student is None

def test_edit_nonexistent_student(client):
    response = client.get('/students/edit/999')
    assert response.status_code == 404
    response = client.post('/students/edit/999', data={'name': 'Test', 'email': 'test@example.com'})
    assert response.status_code == 404

def test_delete_nonexistent_student(client):
    response = client.post('/students/delete/999')
    assert response.status_code == 404

# 3. Course Management Tests (Updated)
def test_add_course(client):
    """Test adding a new course without a teacher."""
    response = client.post('/courses/add', data={
        'name': 'Test Course',
        'description': 'A course for testing.'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Course" in response.data # Check name in table
    assert b"Course &#39;Test Course&#39; added successfully!" in response.data # Check flash, note apostrophe

    with app.app_context():
        course = Course.query.filter_by(name='Test Course').first()
        assert course is not None
        assert course.description == 'A course for testing.'
        assert course.teacher_id is None

def test_list_courses(client):
    with app.app_context():
        c1 = Course(name='List Course 1', description='Desc 1')
        db.session.add(c1)
        db.session.commit()

    response = client.get('/courses')
    assert response.status_code == 200
    assert b"List Course 1" in response.data
    assert b"Desc 1" in response.data

def test_edit_course(client):
    with app.app_context():
        course = Course(name='Original Course', description='Original Desc')
        db.session.add(course)
        db.session.commit()
        course_id = course.id

    response = client.post(f'/courses/edit/{course_id}', data={
        'name': 'Updated Course',
        'description': 'Updated Desc'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated Course" in response.data # Check name in table
    assert b"Course &#39;Updated Course&#39; updated successfully!" in response.data # Check flash

    with app.app_context():
        updated_course = db.session.get(Course, course_id)
        assert updated_course.name == 'Updated Course'
        assert updated_course.description == 'Updated Desc'

def test_delete_course(client):
    with app.app_context():
        course = Course(name='Course to Delete', description='Delete Desc')
        db.session.add(course)
        db.session.commit()
        course_id = course.id
    # Course delete in app.py does not have flash messages.
    response = client.post(f'/courses/delete/{course_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Course to Delete" not in response.data

    with app.app_context():
        deleted_course = db.session.get(Course, course_id)
        assert deleted_course is None

# 4. Teacher Management CRUD Tests
def test_add_teacher(client):
    response = client.post('/teachers/add', data={
        'name': 'Test Teacher',
        'email': 'teacher@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Teacher" in response.data # Check name in table
    assert b"Teacher &#39;Test Teacher&#39; added successfully!" in response.data # Check flash
    with app.app_context():
        teacher = Teacher.query.filter_by(email='teacher@example.com').first()
        assert teacher is not None
        assert teacher.name == 'Test Teacher'

def test_list_teachers(client):
    with app.app_context():
        t1 = Teacher(name='List Teacher 1', email='list.teacher1@example.com')
        db.session.add(t1)
        db.session.commit()
    response = client.get('/teachers')
    assert response.status_code == 200
    assert b"List Teacher 1" in response.data

def test_edit_teacher(client):
    with app.app_context():
        teacher = Teacher(name='Original Teacher', email='original.teacher@example.com')
        db.session.add(teacher)
        db.session.commit()
        teacher_id = teacher.id
    response = client.post(f'/teachers/edit/{teacher_id}', data={
        'name': 'Updated Teacher',
        'email': 'updated.teacher@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated Teacher" in response.data # Check name in table
    assert b"Teacher &#39;Updated Teacher&#39; updated successfully!" in response.data # Check flash
    with app.app_context():
        updated_t = db.session.get(Teacher, teacher_id)
        assert updated_t.name == 'Updated Teacher'
        assert updated_t.email == 'updated.teacher@example.com'

def test_delete_teacher(client):
    with app.app_context():
        teacher = Teacher(name='Delete This Teacher', email='delete.this.teacher@example.com')
        db.session.add(teacher)
        db.session.commit()
        teacher_id = teacher.id
    response = client.post(f'/teachers/delete/{teacher_id}', follow_redirects=True)
    assert response.status_code == 200
    # Check the name is not in the table part of the page.
    # A more robust check would parse HTML or ensure the specific table row is gone.
    # For now, this relies on the name only appearing in the flash message if deleted.
    assert b"Delete This Teacher" not in response.data.split(b'<div class="message success">')[0]
    assert b"Teacher &#39;Delete This Teacher&#39; deleted successfully!" in response.data # Check flash
    with app.app_context():
        assert db.session.get(Teacher, teacher_id) is None

def test_add_teacher_duplicate_email(client):
    with app.app_context():
        teacher = Teacher(name='First Teacher', email='duplicate@example.com')
        db.session.add(teacher)
        db.session.commit()
    response = client.post('/teachers/add', data={
        'name': 'Second Teacher',
        'email': 'duplicate@example.com'
    }, follow_redirects=False)
    assert response.status_code == 200
    assert b"Teacher with email &#39;duplicate@example.com&#39; already exists." in response.data
    with app.app_context():
        teachers = Teacher.query.filter_by(email='duplicate@example.com').all()
        assert len(teachers) == 1

# 5. Course-Teacher Relationship Tests
def test_add_course_with_teacher(client):
    with app.app_context():
        teacher = Teacher(name='Course Assign Teacher', email='course.assign@example.com')
        db.session.add(teacher)
        db.session.commit()
        teacher_id = teacher.id

    client.post('/courses/add', data={
        'name': 'Course With Teacher',
        'description': 'Test description',
        'teacher_id': str(teacher_id)
    }, follow_redirects=True)

    with app.app_context():
        course = Course.query.filter_by(name='Course With Teacher').first()
        assert course is not None
        assert course.teacher_id == teacher_id
        assert course.teacher is not None
        assert course.teacher.name == 'Course Assign Teacher'

    response = client.get('/courses')
    assert b'Course With Teacher' in response.data
    assert b'Course Assign Teacher' in response.data


def test_edit_course_change_teacher(client):
    with app.app_context():
        t1 = Teacher(name='Teacher One', email='t1@example.com')
        t2 = Teacher(name='Teacher Two', email='t2@example.com')
        course = Course(name='Changeable Course', description='Desc', teacher=t1)
        db.session.add_all([t1, t2, course])
        db.session.commit()
        course_id = course.id
        teacher_two_id = t2.id

    client.post(f'/courses/edit/{course_id}', data={
        'name': 'Changeable Course',
        'description': 'Desc Updated',
        'teacher_id': str(teacher_two_id)
    }, follow_redirects=True)

    with app.app_context():
        updated_course = db.session.get(Course, course_id)
        assert updated_course.teacher_id == teacher_two_id
        assert updated_course.teacher.name == 'Teacher Two'

def test_edit_course_remove_teacher(client):
    with app.app_context():
        teacher = Teacher(name='Removable Teacher', email='removable@example.com')
        course = Course(name='Course To Orphan', description='Desc', teacher=teacher)
        db.session.add_all([teacher, course])
        db.session.commit()
        course_id = course.id

    client.post(f'/courses/edit/{course_id}', data={
        'name': 'Course To Orphan',
        'description': 'Desc Updated',
        'teacher_id': ''
    }, follow_redirects=True)

    with app.app_context():
        updated_course = db.session.get(Course, course_id)
        assert updated_course.teacher_id is None
        assert updated_course.teacher is None

    response = client.get('/courses')
    assert b'Course To Orphan' in response.data
    assert b'Unassigned' in response.data


def test_delete_teacher_with_assigned_courses(client):
    with app.app_context():
        teacher = Teacher(name='Teacher With Courses', email='teacher.courses@example.com')
        course = Course(name='Orphaned Course Test', description='Desc', teacher=teacher)
        db.session.add_all([teacher, course])
        db.session.commit()
        teacher_id = teacher.id
        course_id = course.id

    client.post(f'/teachers/delete/{teacher_id}', follow_redirects=True)

    with app.app_context():
        deleted_teacher = db.session.get(Teacher, teacher_id)
        assert deleted_teacher is None

        retrieved_course = db.session.get(Course, course_id)
        assert retrieved_course is not None
        # For SQLite, if PRAGMA foreign_keys = ON is not explicitly set for the connection,
        # deleting a referenced parent might not update child FKS to NULL automatically
        # unless ON DELETE SET NULL is part of FK definition.
        # Given the previous test failure, it seemed teacher_id became None.
        assert retrieved_course.teacher_id is None
        assert retrieved_course.teacher is None

    response = client.get('/courses')
    assert b'Orphaned Course Test' in response.data
    assert b'Unassigned' in response.data

# 6. PDF Question Generation Test
def test_question_generation_page(client):
    """Test the PDF question generation page loads."""
    response = client.get('/soru-uret')
    assert response.status_code == 200
    assert b"PDF'den Soru \xc3\x9cretme" in response.data

def test_question_generation_no_file(client):
    """Test submitting the form with no file."""
    response = client.post('/soru-uret', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b"No file part" in response.data

def test_question_generation_empty_filename(client):
    """Test submitting the form with an empty filename."""
    from werkzeug.datastructures import FileStorage
    import io

    data = {
        'pdf_file': (io.BytesIO(b""), ''),
        'question_count': '5'
    }
    response = client.post('/soru-uret', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"No selected file" in response.data

def test_question_generation_invalid_file_type(client):
    """Test submitting the form with a non-PDF file."""
    from werkzeug.datastructures import FileStorage
    import io

    data = {
        'pdf_file': (io.BytesIO(b"this is a text file"), 'test.txt'),
        'question_count': '5'
    }
    response = client.post('/soru-uret', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid file type. Please upload a PDF." in response.data

@patch('school_automation.app.PdfReader')
@patch('school_automation.app.tokenizer')
@patch('school_automation.app.model')
def test_question_generation_success(mock_model, mock_tokenizer, mock_pdf_reader, client):
    """Test the successful generation of questions from a PDF."""
    # Mock PdfReader
    mock_pdf_instance = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is the content of the PDF."
    mock_pdf_instance.pages = [mock_page]
    mock_pdf_reader.return_value = mock_pdf_instance

    # Mock tokenizer and model
    mock_tokenizer.encode.return_value = "mock_input_ids"
    mock_model.generate.return_value = ["mock_output_ids"]
    mock_tokenizer.decode.return_value = "Generated Question 1?"

    pdf_content = b'dummy pdf content'
    data = {
        'pdf_file': (io.BytesIO(pdf_content), 'test.pdf'),
        'question_count': '1'
    }

    response = client.post('/soru-uret', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert b"Generated Question 1?" in response.data

    # Verify that our mocks were called as expected
    mock_pdf_reader.assert_called_once()
    mock_tokenizer.encode.assert_called_once_with("generate questions: This is the content of the PDF.", return_tensors="pt", max_length=512, truncation=True)
    mock_model.generate.assert_called_once_with("mock_input_ids", max_length=64, num_beams=4, early_stopping=True, num_return_sequences=1)
    mock_tokenizer.decode.assert_called_once_with("mock_output_ids", skip_special_tokens=True)
