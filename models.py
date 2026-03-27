from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

db = SQLAlchemy()


# ============================================================
# ПОЛЬЗОВАТЕЛИ
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    photo = db.Column(db.String(255), default='default_avatar.png')  # только имя файла
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    itcoins = db.Column(db.Integer, default=0)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_parent(self):
        return self.role == 'parent'

    def get_photo_url(self):
        """Возвращает путь к фото для статики"""
        if self.photo and self.photo != 'default_avatar.png':
            return f'uploads/users/{self.photo}'
        return 'uploads/users/default_avatar.png'


# ============================================================
# РОДИТЕЛИ (связь родитель-ребенок)
# ============================================================
class Parent(db.Model):
    __tablename__ = 'parents'
    
    id = db.Column(db.Integer, primary_key=True)
    id_parent = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_child = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    parent = db.relationship('User', foreign_keys=[id_parent], backref='my_children')
    child = db.relationship('User', foreign_keys=[id_child], backref='my_parent')


# ============================================================
# МОДУЛИ
# ============================================================
class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(255), default='default_module.png')  # только имя файла
    icon = db.Column(db.String(50), default='book')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lessons_list = db.relationship('Lesson', backref='parent_module', lazy=True, cascade='all, delete-orphan')
    groups_list = db.relationship('Group', backref='parent_module', lazy=True, cascade='all, delete-orphan')
    progress_list = db.relationship('ProgressModule', backref='parent_module', lazy=True, cascade='all, delete-orphan')
    
    def get_photo_url(self):
        """Возвращает путь к фото модуля"""
        if self.photo and self.photo != 'default_module.png':
            return f'uploads/modules/{self.photo}'
        return 'uploads/modules/default_module.png'



class GroupStudent(db.Model):
    __tablename__ = 'group_students'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    group = db.relationship('Group', backref='group_students')
    student = db.relationship('User', foreign_keys=[student_id], backref='student_groups')
    
    __table_args__ = (db.UniqueConstraint('group_id', 'student_id', name='unique_group_student'),)

# ============================================================
# ГРУППЫ ОБУЧЕНИЯ
# ============================================================


class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')
    # module - через backref 'parent_module'
    # group_students - будет через backref
    # chat - через backref 'chat_list'
    
    def get_students(self):
        """Получить всех учеников группы"""
        return [gs.student for gs in self.group_students]
    
    def get_chat(self):
        """Получить чат группы"""
        return Chat.query.filter_by(group_id=self.id).first()
    
    def add_student(self, student):
        """Добавить ученика в группу"""
        existing = GroupStudent.query.filter_by(group_id=self.id, student_id=student.id).first()
        if existing:
            return False
        gs = GroupStudent(group_id=self.id, student_id=student.id)
        db.session.add(gs)
        db.session.commit()
        return True
    
    def remove_student(self, student):
        """Удалить ученика из группы"""
        gs = GroupStudent.query.filter_by(group_id=self.id, student_id=student.id).first()
        if gs:
            db.session.delete(gs)
            db.session.commit()
            return True
        return False
    
    def has_student(self, student):
        """Проверить, есть ли ученик в группе"""
        return GroupStudent.query.filter_by(group_id=self.id, student_id=student.id).first() is not None


# ============================================================
# УРОКИ
# ============================================================
class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    
    # Связи
    theory_list = db.relationship('Theory', backref='parent_lesson', lazy=True, cascade='all, delete-orphan')
    tests_list = db.relationship('Test', backref='parent_lesson', lazy=True, cascade='all, delete-orphan')
    tasks_list = db.relationship('Task', backref='parent_lesson', lazy=True, cascade='all, delete-orphan')


# ============================================================
# ТЕОРИЯ
# ============================================================
class Theory(db.Model):
    __tablename__ = 'theory'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    image = db.Column(db.String(255), default='default_theory.png')  # только имя файла
    
    def get_image_url(self):
        """Возвращает путь к изображению теории"""
        if self.image and self.image != 'default_theory.png':
            return f'uploads/theories/{self.image}'
        return 'uploads/theories/default_theory.png'


# ============================================================
# ТЕСТЫ
# ============================================================
class Test(db.Model):
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text)
    type = db.Column(db.String(30), default='single')
    answer = db.Column(db.Text)
    options = db.Column(db.JSON, default=list)
    
    options_list = db.relationship('Option', backref='parent_test', lazy=True, cascade='all, delete-orphan')
    results_list = db.relationship('TestResult', backref='parent_test', lazy=True, cascade='all, delete-orphan')


# ============================================================
# ВАРИАНТЫ ОТВЕТОВ
# ============================================================
class Option(db.Model):
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)


# ============================================================
# ЗАДАНИЯ
# ============================================================
class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    image = db.Column(db.String(255))
    
    results_list = db.relationship('TaskResult', backref='parent_task', lazy=True, cascade='all, delete-orphan')


# ============================================================
# РЕЗУЛЬТАТЫ ТЕСТОВ
# ============================================================
class TestResult(db.Model):
    __tablename__ = 'tests_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    answer = db.Column(db.JSON, default=list)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='test_results')


# ============================================================
# РЕЗУЛЬТАТЫ ЗАДАНИЙ
# ============================================================
class TaskResult(db.Model):
    __tablename__ = 'tasks_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    status = db.Column(db.String(30), default='pending')
    bonus_coin = db.Column(db.Integer, default=0)
    comment = db.Column(db.Text)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='task_results')

class ProgressModule(db.Model):
    __tablename__ = 'progress_module'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    progress = db.Column(db.JSON, default=dict)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='progress_modules')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'module_id', name='unique_user_module'),)
    
    def init_progress(self, module):
        """Инициализирует структуру прогресса на основе модуля"""
        progress_data = {
            'percentage': 0,
            'completed_lessons': [],
            'current_lesson': None,
            'lessons': {}
        }
        
        for lesson in module.lessons_list:
            lesson_data = {
                'title': lesson.title,
                'completed': False,
                'started': False,
                'tests': {},
                'tasks': {},
                'theory_viewed': False
            }
            
            for test in lesson.tests_list:
                lesson_data['tests'][str(test.id)] = {
                    'title': test.title,
                    'completed': False,
                    'score': 0,
                    'attempts': 0,
                    'last_answer': None,
                    'is_correct': False
                }
            
            for task in lesson.tasks_list:
                lesson_data['tasks'][str(task.id)] = {
                    'title': task.title,
                    'completed': False,
                    'submitted': False,
                    'score': 0
                }
            
            progress_data['lessons'][str(lesson.id)] = lesson_data
        
        self.progress = progress_data
        return progress_data
    
    def start_lesson(self, lesson_id):
        """Отмечает начало урока"""
        lesson_id_str = str(lesson_id)
        
        if 'lessons' not in self.progress:
            return False
        
        if lesson_id_str in self.progress.get('lessons', {}):
            self.progress['lessons'][lesson_id_str]['started'] = True
            self.progress['current_lesson'] = lesson_id_str
            return True
        return False
    
    def update_percentage(self):
        """Обновляет процент выполнения модуля"""
        if not self.progress or 'lessons' not in self.progress:
            return 0
        
        total_lessons = len(self.progress['lessons'])
        if total_lessons == 0:
            return 0
        
        completed_lessons = len(self.progress.get('completed_lessons', []))
        percentage = int((completed_lessons / total_lessons) * 100)
        self.progress['percentage'] = percentage
        return percentage
    
    def complete_lesson(self, lesson_id):
        """Отмечает урок как пройденный"""
        lesson_id_str = str(lesson_id)
        
        if lesson_id_str not in self.progress.get('lessons', {}):
            return False
        
        if lesson_id_str not in self.progress.get('completed_lessons', []):
            self.progress['completed_lessons'].append(lesson_id_str)
        
        self.progress['lessons'][lesson_id_str]['completed'] = True
        
        self.update_percentage()
        
        if len(self.progress['completed_lessons']) == len(self.progress['lessons']):
            self.completed_at = datetime.utcnow()
        
        return True
    
    def get_lesson_progress(self, lesson_id):
        """Получает прогресс по конкретному уроку с деталями"""
        lesson_id_str = str(lesson_id)
        
        default_result = {
            'percentage': 0,
            'completed_items': 0,
            'total_items': 0,
            'details': {
                'theory': {'completed': False, 'required': True},
                'tests': [],
                'tasks': []
            }
        }
        
        if 'lessons' not in self.progress:
            return default_result
        
        if lesson_id_str not in self.progress.get('lessons', {}):
            return default_result
        
        lesson = self.progress['lessons'][lesson_id_str]
        
        total_items = 0
        completed_items = 0
        details = {
            'theory': {'completed': False, 'required': True},
            'tests': [],
            'tasks': []
        }
        
        # Теория
        total_items += 1
        if lesson.get('theory_viewed', False):
            completed_items += 1
            details['theory']['completed'] = True
        
        # Тесты
        for test_id, test_data in lesson.get('tests', {}).items():
            total_items += 1
            test_detail = {
                'id': test_id,
                'title': test_data.get('title', 'Тест'),
                'completed': test_data.get('completed', False),
                'is_correct': test_data.get('is_correct', False),
                'last_answer': test_data.get('last_answer', None),
                'score': test_data.get('score', 0),
                'attempts': test_data.get('attempts', 0)
            }
            details['tests'].append(test_detail)
            if test_data.get('completed', False):
                completed_items += 1
        
        # Задания
        for task_id, task_data in lesson.get('tasks', {}).items():
            total_items += 1
            task_detail = {
                'id': task_id,
                'title': task_data.get('title', 'Задание'),
                'completed': task_data.get('completed', False),
                'submitted': task_data.get('submitted', False),
                'score': task_data.get('score', 0)
            }
            details['tasks'].append(task_detail)
            if task_data.get('completed', False):
                completed_items += 1
        
        lesson_percent = int((completed_items / total_items) * 100) if total_items > 0 else 0
        
        return {
            'percentage': lesson_percent,
            'completed_items': completed_items,
            'total_items': total_items,
            'details': details
        }
    
    def complete_test(self, test_id, user_answer, is_correct, score=100):
        """Отмечает тест как пройденный с сохранением ответа"""
        test_id_str = str(test_id)
        
        if 'lessons' not in self.progress:
            return False, False  # возвращаем (успешно, уже был пройден)
        
        for lesson_id, lesson_data in self.progress.get('lessons', {}).items():
            if test_id_str in lesson_data.get('tests', {}):
                test_data = lesson_data['tests'][test_id_str]
                
                # Проверяем, был ли тест уже пройден
                already_completed = test_data.get('completed', False)
                
                if already_completed:
                    # Тест уже пройден, не начисляем ITCoins повторно
                    return True, False  # успешно, но без начисления
                
                # Сохраняем результат теста с ответом
                test_data['completed'] = True
                test_data['score'] = score
                test_data['attempts'] = test_data.get('attempts', 0) + 1
                test_data['last_answer'] = user_answer
                test_data['is_correct'] = is_correct
                
                # Проверяем, все ли тесты в уроке пройдены
                all_tests_completed = all(
                    t_data['completed'] 
                    for t_data in lesson_data['tests'].values()
                )
                
                # Если все тесты пройдены и теория просмотрена, отмечаем урок как завершенный
                if all_tests_completed and lesson_data.get('theory_viewed', False):
                    self.complete_lesson(int(lesson_id))
                
                return True, True  # успешно и начисляем ITCoins
        
        return False, False
    
    def view_theory(self, lesson_id):
        """Отмечает просмотр теории"""
        lesson_id_str = str(lesson_id)
        
        if 'lessons' not in self.progress:
            return False
        
        if lesson_id_str in self.progress.get('lessons', {}):
            self.progress['lessons'][lesson_id_str]['theory_viewed'] = True
            
            # Проверяем, можно ли завершить урок
            lesson = self.progress['lessons'][lesson_id_str]
            all_tests_completed = all(
                test_data['completed'] 
                for test_data in lesson.get('tests', {}).values()
            )
            all_tasks_completed = all(
                task_data['completed'] 
                for task_data in lesson.get('tasks', {}).values()
            )
            
            if all_tests_completed and all_tasks_completed:
                self.complete_lesson(int(lesson_id))
            
            return True
        return False
    
    def get_test_result(self, test_id):
        """Получает результат конкретного теста"""
        test_id_str = str(test_id)
        
        if 'lessons' not in self.progress:
            return None
        
        for lesson_id, lesson_data in self.progress.get('lessons', {}).items():
            if test_id_str in lesson_data.get('tests', {}):
                return lesson_data['tests'][test_id_str]
        
        return None


# ============================================================
# ЧАТЫ
# ============================================================
class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    users = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_chats')
    group = db.relationship('Group', foreign_keys=[group_id], backref='chat_list')
    messages_list = db.relationship('Message', backref='parent_chat', lazy=True, cascade='all, delete-orphan')


# ============================================================
# СООБЩЕНИЯ
# ============================================================
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    title = db.Column(db.String(100))
    text = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='user_messages')