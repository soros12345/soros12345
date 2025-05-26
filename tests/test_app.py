import pytest
from school_automation.app import app, students_db, courses_db # Import app and dbs

# Revised fixture as per instructions
@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Flask's app_context is needed for url_for and other app-specific functions
    with app.app_context(): 
        with app.test_client() as client:
            students_db.clear()
            courses_db.clear()
            # Note: next_student_id and next_course_id are not reset here.
            # Tests will need to work with incrementing IDs.
            yield client

# 1. Home Page Test
def test_home_page(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Manage Students" in response.data
    assert b"Manage Courses" in response.data

# 2. Student Management Tests
def test_add_student(client):
    """Test adding a new student."""
    response = client.post('/students/add', data={
        'name': 'Test Student',
        'email': 'test.student@example.com'
    }, follow_redirects=False) # Test redirect first
    assert response.status_code == 302
    assert response.location == '/students'

    # Check if student is in the database (ID will be the current next_student_id)
    # Since IDs are not reset, we assume it's the first student added in this test context
    # or we find it by name if multiple tests run sequentially without app context recreation per test.
    # For simplicity, this test assumes it's the only one adding this specific student.
    assert len(students_db) == 1
    assert students_db[0]['name'] == 'Test Student'
    assert students_db[0]['email'] == 'test.student@example.com'
    
    # Follow redirect to check if student name is on the list page
    response_redirect = client.get('/students')
    assert response_redirect.status_code == 200
    assert b"Test Student" in response_redirect.data
    assert b"test.student@example.com" in response_redirect.data


def test_list_students(client):
    """Test listing students."""
    # Add a student directly for testing (or use the add endpoint)
    # Since IDs are not reset, we must be careful.
    # Let's use the endpoint to ensure next_student_id is handled by app logic
    client.post('/students/add', data={'name': 'List Test Student', 'email': 'list.test@example.com'})
    
    response = client.get('/students')
    assert response.status_code == 200
    assert b"List Test Student" in response.data
    assert b"list.test@example.com" in response.data

def test_edit_student(client):
    """Test editing an existing student."""
    # Add a student first
    client.post('/students/add', data={'name': 'Edit Original Name', 'email': 'edit.original@example.com'})
    student_id_to_edit = students_db[0]['id'] # Get the ID of the added student

    response = client.post(f'/students/edit/{student_id_to_edit}', data={
        'name': 'Edit Updated Name',
        'email': 'edit.updated@example.com'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/students'

    # Verify student_db shows updated information
    updated_student = None
    for s in students_db:
        if s['id'] == student_id_to_edit:
            updated_student = s
            break
    assert updated_student is not None
    assert updated_student['name'] == 'Edit Updated Name'
    assert updated_student['email'] == 'edit.updated@example.com'

def test_delete_student(client):
    """Test deleting an existing student."""
    # Add a student first
    client.post('/students/add', data={'name': 'Delete Test Student', 'email': 'delete.test@example.com'})
    student_to_delete = students_db[0] # Get the student
    student_id_to_delete = student_to_delete['id']

    response = client.post(f'/students/delete/{student_id_to_delete}', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/students'

    # Verify student is removed from students_db
    assert student_to_delete not in students_db
    
    # Verify the student is not on the list page
    response_redirect = client.get('/students')
    assert response_redirect.status_code == 200
    assert b"Delete Test Student" not in response_redirect.data


def test_edit_nonexistent_student(client):
    """Test editing a non-existent student."""
    response_get = client.get('/students/edit/9999') # High ID likely not to exist
    assert response_get.status_code == 404
    
    response_post = client.post('/students/edit/9999', data={
        'name': 'Non Existent',
        'email': 'non.existent@example.com'
    })
    assert response_post.status_code == 404

def test_delete_nonexistent_student(client):
    """Test deleting a non-existent student."""
    response = client.post('/students/delete/9999') # High ID likely not to exist
    assert response.status_code == 404


# 3. Course Management Tests
def test_add_course(client):
    """Test adding a new course."""
    response = client.post('/courses/add', data={
        'name': 'Test Course',
        'description': 'A course for testing.',
        'teacher_id': '101'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/courses'

    assert len(courses_db) == 1
    assert courses_db[0]['name'] == 'Test Course'
    assert courses_db[0]['description'] == 'A course for testing.'
    assert courses_db[0]['teacher_id'] == '101'

    response_redirect = client.get('/courses')
    assert response_redirect.status_code == 200
    assert b"Test Course" in response_redirect.data
    assert b"A course for testing." in response_redirect.data


def test_list_courses(client):
    """Test listing courses."""
    client.post('/courses/add', data={'name': 'List Test Course', 'description': 'Desc for list test', 'teacher_id': '102'})
    
    response = client.get('/courses')
    assert response.status_code == 200
    assert b"List Test Course" in response.data
    assert b"Desc for list test" in response.data

def test_edit_course(client):
    """Test editing an existing course."""
    client.post('/courses/add', data={'name': 'Original Course Name', 'description': 'Original Desc', 'teacher_id': '103'})
    course_id_to_edit = courses_db[0]['id']

    response = client.post(f'/courses/edit/{course_id_to_edit}', data={
        'name': 'Updated Course Name',
        'description': 'Updated Desc',
        'teacher_id': '104'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/courses'

    updated_course = None
    for c in courses_db:
        if c['id'] == course_id_to_edit:
            updated_course = c
            break
    assert updated_course is not None
    assert updated_course['name'] == 'Updated Course Name'
    assert updated_course['description'] == 'Updated Desc'
    assert updated_course['teacher_id'] == '104'

def test_delete_course(client):
    """Test deleting an existing course."""
    client.post('/courses/add', data={'name': 'Delete Test Course', 'description': 'Delete Desc', 'teacher_id': '105'})
    course_to_delete = courses_db[0]
    course_id_to_delete = course_to_delete['id']

    response = client.post(f'/courses/delete/{course_id_to_delete}', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == '/courses'

    assert course_to_delete not in courses_db
    
    response_redirect = client.get('/courses')
    assert response_redirect.status_code == 200
    assert b"Delete Test Course" not in response_redirect.data

def test_edit_nonexistent_course(client):
    """Test editing a non-existent course."""
    response_get = client.get('/courses/edit/8888')
    assert response_get.status_code == 404
    
    response_post = client.post('/courses/edit/8888', data={
        'name': 'Non Existent Course',
        'description': 'Non Existent Desc'
    })
    assert response_post.status_code == 404

def test_delete_nonexistent_course(client):
    """Test deleting a non-existent course."""
    response = client.post('/courses/delete/8888')
    assert response.status_code == 404
