import os
from flask import Flask, current_app, json, render_template, redirect, url_for, flash, request
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.exceptions import Forbidden
from functools import wraps
from datetime import date, datetime

from config import Config
from models import db, User, Parent, Module, Group, Lesson, Theory, Test, Option, Task, TestResult, TaskResult, ProgressModule, Chat, Message, GroupStudent
from forms import RegistrationForm, LoginForm, UserEditForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему'


# ============================================================
# КОНТЕКСТНЫЙ ПРОЦЕССОР
# ============================================================
@app.context_processor
def utility_processor():
    return {'now': datetime.now()}


# ============================================================
# ФУНКЦИИ ДЛЯ СОЗДАНИЯ ДЕФОЛТНЫХ ДАННЫХ
# ============================================================
def create_default_users():
    """Создает базовых пользователей, если их нет в базе"""

    default_users = [
        {
            'username': 'admin',
            'email': 'admin@yandex.ru',
            'password': '123456',
            'role': 'admin',
            'itcoins': 1000
        },
        {
            'username': 'teacher',
            'email': 'teacher@yandex.ru',
            'password': '123456',
            'role': 'teacher',
            'itcoins': 500
        },
        {
            'username': 'student',
            'email': 'student@yandex.ru',
            'password': '123456',
            'role': 'student',
            'itcoins': 100
        },
        {
            'username': 'parent',
            'email': 'parent@yandex.ru',
            'password': '123456',
            'role': 'parent',
            'itcoins': 0
        }
    ]

    created_users = []

    for user_data in default_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()

        if not existing_user:
            new_user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                is_active=True,
                itcoins=user_data['itcoins']
            )
            new_user.set_password(user_data['password'])
            db.session.add(new_user)
            created_users.append(new_user)
            print(
                f"✅ Создан пользователь: {user_data['username']} ({user_data['role']}) / пароль: 123456")
        else:
            print(f"⏭️  Пользователь уже существует: {user_data['username']}")

    if created_users:
        db.session.commit()

        # Создаем связь родитель-ребенок
        parent = User.query.filter_by(email='parent@yandex.ru').first()
        student = User.query.filter_by(email='student@yandex.ru').first()

        if parent and student:
            existing_relation = Parent.query.filter_by(
                id_parent=parent.id, id_child=student.id).first()
            if not existing_relation:
                parent_rel = Parent(id_parent=parent.id, id_child=student.id)
                db.session.add(parent_rel)
                db.session.commit()
                print("✅ Создана связь: parent → student")

    print("\n📝 Данные для входа (все пароли: 123456):")
    for user_data in default_users:
        print(
            f"   {user_data['username']}: {user_data['email']} / роль: {user_data['role']}")

    return len(created_users)


def create_demo_content():
    """Создает демо-контент, если его нет"""

    if Module.query.count() > 0:
        print("⏭️  Демо-контент уже существует")
        return

    print("📚 Создаем демо-контент...")

    teacher = User.query.filter_by(email='teacher@yandex.ru').first()
    student = User.query.filter_by(email='student@yandex.ru').first()

    # 1. Создаем модуль
    module = Module(
        title="Основы Python",
        description="Изучаем основы программирования на Python с нуля",
        photo="default_module.png"
    )
    db.session.add(module)
    db.session.commit()
    print("✅ Модуль: Основы Python")

    # 2. Создаем уроки
    lesson1 = Lesson(
        module_id=module.id,
        title="Введение в Python",
        content="Python - это простой и мощный язык программирования. Он идеально подходит для начинающих."
    )
    db.session.add(lesson1)

    lesson2 = Lesson(
        module_id=module.id,
        title="Переменные и типы данных",
        content="В Python есть разные типы данных: числа, строки, списки и другие."
    )
    db.session.add(lesson2)
    db.session.commit()
    print("✅ Уроки созданы")

    # 3. Создаем теорию
    theory1 = Theory(
        lesson_id=lesson1.id,
        title="Что такое Python?",
        content="Python был создан Гвидо ван Россумом в 1991 году. Это интерпретируемый язык программирования.",
        image="default_theory.png"
    )
    db.session.add(theory1)

    theory2 = Theory(
        lesson_id=lesson1.id,
        title="Где используется Python?",
        content="Python используется в веб-разработке, анализе данных, искусственном интеллекте и многих других областях.",
        image="default_theory.png"
    )
    db.session.add(theory2)
    db.session.commit()
    print("✅ Теория создана")

    # 4. Создаем тесты
    test1 = Test(
        lesson_id=lesson1.id,
        title="Проверка знаний: Введение",
        text="Кто создал язык программирования Python?",
        type="single",
        answer="Гвидо ван Россум",
        options=["Гвидо ван Россум", "Деннис Ритчи",
                 "Джеймс Гослинг", "Бьёрн Страуструп"]
    )
    db.session.add(test1)

    test2 = Test(
        lesson_id=lesson1.id,
        title="Проверка знаний: Применение",
        text="В каких областях используется Python? (Выберите все подходящие)",
        type="multiple",
        answer="Веб-разработка,ИИ,Анализ данных",
        options=["Веб-разработка", "Мобильные приложения",
                 "Искусственный интеллект", "Анализ данных"]
    )
    db.session.add(test2)
    db.session.commit()
    print("✅ Тесты созданы")

    # 5. Создаем варианты ответов
    for test in [test1, test2]:
        for opt in test.options:
            option = Option(
                test_id=test.id,
                text=opt
            )
            db.session.add(option)
    db.session.commit()
    print("✅ Варианты ответов созданы")

    # 6. Создаем задания
    task1 = Task(
        lesson_id=lesson1.id,
        title="Hello, World!",
        description="Напишите программу, которая выводит на экран фразу 'Hello, World!'",
        link="https://replit.com",
        image="hello_world.png"
    )
    db.session.add(task1)

    task2 = Task(
        lesson_id=lesson2.id,
        title="Переменная с именем",
        description="Создайте переменную name и присвойте ей ваше имя. Выведите приветствие.",
        link="https://replit.com",
        image="variables.png"
    )
    db.session.add(task2)
    db.session.commit()
    print("✅ Задания созданы")

    # 7. Создаем группу
    if teacher:
        group = Group(
            module_id=module.id,
            title="Группа Python: Начинающие",
            date=date(2024, 4, 1),
            created_by=teacher.id
        )
        db.session.add(group)
        db.session.commit()
        print("✅ Группа создана")

        # 8. Создаем чат для группы
        chat = Chat(
            group_id=group.id,
            admin_id=teacher.id,
            title=f"Чат: {group.title}",
            users=[teacher.id, student.id] if student else [teacher.id]
        )
        db.session.add(chat)
        db.session.commit()
        print("✅ Чат создан")

        # 9. Добавляем сообщение
        message = Message(
            user_id=teacher.id,
            chat_id=chat.id,
            title="Добро пожаловать!",
            text="Приветствую всех в нашей группе! Начинаем изучение Python. Если есть вопросы - задавайте!"
        )
        db.session.add(message)
        db.session.commit()
        print("✅ Приветственное сообщение добавлено")

    print("✅ Демо-контент успешно создан!")


# ============================================================
# ЗАГРУЗЧИК ПОЛЬЗОВАТЕЛЯ
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================
# ДЕКОРАТОР ДЛЯ ПРОВЕРКИ РОЛЕЙ
# ============================================================
def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))

            if current_user.role not in roles:
                flash('У вас нет доступа к этой странице', 'danger')
                if request.endpoint == 'dashboard':
                    return redirect(url_for('index'))
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# ОСНОВНЫЕ МАРШРУТЫ
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='student',
            is_active=True,
            itcoins=100
        )
        user.set_password(form.password.data)

        if User.query.count() == 0:
            user.role = 'admin'
            user.itcoins = 1000

        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html', form=form)


def sync_user_chats(user):
    """Синхронизирует чаты пользователя со всеми группами, где он состоит"""
    from models import Group, GroupStudent, Chat

    print(f"Синхронизация чатов для {user.username}...")

    # Находим все группы через таблицу group_students
    groups = db.session.query(Group).join(GroupStudent).filter(
        GroupStudent.student_id == user.id).all()
    print(f"  Найдено групп: {len(groups)}")

    for group in groups:
        print(f"  Группа: {group.title}")
        chat = Chat.query.filter_by(group_id=group.id).first()

        if chat:
            if chat.users is None:
                chat.users = []
            if user.id not in chat.users:
                chat.users.append(user.id)
                print(f"    ✅ Добавлен в чат")
            else:
                print(f"    ⏭️ Уже в чате")
        else:
            # Создаем чат, если его нет
            chat = Chat(
                group_id=group.id,
                admin_id=group.created_by,
                title=f"Чат: {group.title}",
                users=[user.id, group.created_by]
            )
            db.session.add(chat)
            print(f"    ✅ Создан новый чат и добавлен пользователь")

    db.session.commit()
    print(f"Синхронизация завершена")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)

            # Синхронизируем чаты
            sync_user_chats(user)

            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('auth/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Перенаправляет на дашборд в зависимости от роли"""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif current_user.role == 'parent':
        return redirect(url_for('parent_dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        flash(f'Неизвестная роль: {current_user.role}', 'warning')
        return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """Страница профиля пользователя"""

    stats = {}
    if current_user.role == 'student':
        stats['total_lessons'] = Lesson.query.count()
        stats['completed_lessons'] = ProgressModule.query.filter_by(
            user_id=current_user.id).count()
        stats['total_tests'] = Test.query.count()
        stats['completed_tests'] = TestResult.query.filter_by(
            user_id=current_user.id).count()
        stats['total_tasks'] = Task.query.count()
        stats['completed_tasks'] = TaskResult.query.filter_by(
            user_id=current_user.id, status='completed').count()

    teacher_stats = {}
    if current_user.role == 'teacher':
        groups = Group.query.filter_by(created_by=current_user.id).all()
        teacher_stats['groups_count'] = len(groups)
        students_count = 0
        for group in groups:
            students_count += len(group.get_students())
        teacher_stats['students_count'] = students_count

    parent_stats = {}
    if current_user.role == 'parent':
        children = Parent.query.filter_by(id_parent=current_user.id).all()
        parent_stats['children_count'] = len(children)

    recent_activity = []

    return render_template('profile.html',
                           stats=stats,
                           teacher_stats=teacher_stats,
                           parent_stats=parent_stats,
                           recent_activity=recent_activity)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Обновление профиля"""
    username = request.form.get('username')
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if username != current_user.username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Имя пользователя уже занято', 'danger')
            return redirect(url_for('profile'))

    if email != current_user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email уже используется', 'danger')
            return redirect(url_for('profile'))

    current_user.username = username
    current_user.email = email

    if new_password:
        if new_password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('profile'))
        if len(new_password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'danger')
            return redirect(url_for('profile'))
        current_user.set_password(new_password)

    db.session.commit()
    flash('Профиль успешно обновлен!', 'success')
    return redirect(url_for('profile'))


@app.route('/profile/update_photo', methods=['POST'])
@login_required
def update_photo():
    """Обновление фото профиля"""
    if 'photo' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('profile'))

    file = request.files['photo']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('profile'))

    if file:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit(
            '.', 1)[1].lower() if '.' in file.filename else ''

        if ext not in allowed_extensions:
            flash(
                'Неподдерживаемый формат файла. Используйте PNG, JPG, GIF или WEBP', 'danger')
            return redirect(url_for('profile'))

        filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"

        upload_folder = os.path.join(app.config.get(
            'UPLOAD_FOLDER', 'static/uploads'), 'users')
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        if current_user.photo and current_user.photo != 'default_avatar.png':
            old_filepath = os.path.join(upload_folder, current_user.photo)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except:
                    pass

        current_user.photo = filename
        db.session.commit()

        flash('Фото профиля обновлено!', 'success')

    return redirect(url_for('profile'))


# ============================================================
# АДМИН МАРШРУТЫ
# ============================================================
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'teachers': User.query.filter_by(role='teacher').count(),
        'students': User.query.filter_by(role='student').count(),
        'parents': User.query.filter_by(role='parent').count(),
        'modules': Module.query.count(),
        'groups': Group.query.count()
    }

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    popular_modules = Module.query.all()
    all_modules = Module.query.all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           popular_modules=popular_modules,
                           all_modules=all_modules)


@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        flash('Пользователь обновлен', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/edit_user.html', form=form, user=user)


@app.route('/admin/user/<int:user_id>/delete')
@login_required
@role_required('admin')
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Вы не можете удалить самого себя', 'danger')
        return redirect(url_for('admin_users'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удален', 'success')
    return redirect(url_for('admin_users'))


# ============================================================
# Управление ИГРАМИ
# ============================================================

@app.route(f'/game_keyboard_cpp')
@login_required
@role_required('student')
def game_keyboard():
    return render_template(f'games/keyboard_cpp.html')


@app.route(f'/game_keyboard_python')
@login_required
@role_required('student')
def game_keyboard_1():
    return render_template(f'games/keyboard_python.html')


@app.route(f'/game_word_battle')
@login_required
@role_required('student')
def game_word_buttle():
    return render_template(f'games/word_buttle.html')


@app.route('/game_find')
@login_required
@role_required('student')
def game_find_bug():
    return render_template('games/find_bug.html')

# ============================================================
# Управление прогрессом
# ============================================================


@app.route('/student/sertificates/')
@login_required
@role_required('student')
def student_sertificates():

    child_id = current_user.id
    
    # Формируем путь к файлу
    json_folder = os.path.join(current_app.root_path, 'data', 'certificates')
    file_path = os.path.join(json_folder, f"{child_id}.json")
    
    certificates_data = []

    # --- ОТЛАДКА: Выводим путь в консоль ---
    print(f"--- Поиск файла: {file_path}")

    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                certificates_data = json.load(json_file)
                
            # --- ОТЛАДКА: Выводим количество считанных записей ---
            print(f"--- Успешно загружено записей: {len(certificates_data)}")
            print(f"--- Данные: {certificates_data}") 
                
        except json.JSONDecodeError:
            print(f"Ошибка: Файл {file_path} содержит некорректный JSON.")
            certificates_data = []
    else:
        print(f"--- Файл НЕ НАЙДЕН по пути: {file_path}")

    return render_template('student/setrificate.html', certificates=certificates_data)


@app.route('/student/achievements/')
@login_required
@role_required('student')
def student_achievements():

    child_id = current_user.id     

    print("")
    # Папка, где хранятся файлы достижений
    json_folder = os.path.join(current_app.root_path, 'data', 'achievements')
    filename = f"{child_id}.json"
    file_path = os.path.join(json_folder, filename)
    
    achievements_data = []

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                achievements_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка чтения JSON файла {filename}")
    else:
        print(f"Файл достижений для ID {child_id} не найден.")

    return render_template('student/achievements.html', achievements=achievements_data)

@app.route('/student/store')
@login_required
@role_required('student')
def store():
    return render_template('student/store.html')


@app.route('/student/store')
@login_required
@role_required('student')
def store():
    return render_template('student/store.html')


# ========== МАГАЗИН ==========

@app.route('/shop/buy/<int:item_id>', methods=['POST'])
@login_required
def shop_buy(item_id):
    """Покупка товара"""
    import json

    # Получаем данные о товаре (временно жестко задаем)
    items_data = {
        1: {"name": "Подписка CodeQuest Pro", "price": 500},
        2: {"name": "Подписка CodeQuest Premium", "price": 1200},
        3: {"name": "Игровая мышь Logitech G502", "price": 300},
        4: {"name": "Механическая клавиатура", "price": 450},
        5: {"name": "Футболка CodeQuest", "price": 150},
        6: {"name": "Кружка CodeQuest", "price": 80},
        7: {"name": "Sony PlayStation 5", "price": 5000},
        8: {"name": "Наушники Sony WH-1000XM5", "price": 800},
        9: {"name": "Годовой доступ CodeQuest Ultimate", "price": 3500}
    }

    item = items_data.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Товар не найден'}), 404

    if current_user.itcoins < item['price']:
        return jsonify({'success': False, 'message': f'Недостаточно ITCoins! Нужно {item["price"]} ITCoins'}), 400

    # Списываем ITCoins
    current_user.itcoins -= item['price']
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'🎉 Поздравляем! Вы купили {item["name"]} за {item["price"]} ITCoins!',
        'new_balance': current_user.itcoins
    })

# ========== УПРАВЛЕНИЕ МОДУЛЯМИ (АДМИН) ==========


@app.route('/admin/modules')
@login_required
@role_required('admin')
def admin_modules():
    modules = Module.query.all()
    return render_template('admin/modules.html', modules=modules)


@app.route('/admin/module/create', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_module():
    title = request.form.get('title')
    description = request.form.get('description')
    icon = request.form.get('icon', 'book')

    if not title:
        flash('Название модуля обязательно', 'danger')
        return redirect(url_for('admin_modules'))

    module = Module(
        title=title,
        description=description,
        icon=icon,
        photo='default_module.png'
    )

    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = file.filename.rsplit(
                '.', 1)[1].lower() if '.' in file.filename else ''

            if ext in allowed_extensions:
                filename = f"module_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_folder = os.path.join(app.config.get(
                    'UPLOAD_FOLDER', 'static/uploads'), 'modules')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                module.photo = filename

    db.session.add(module)
    db.session.commit()

    flash(f'Модуль "{title}" успешно создан!', 'success')
    return redirect(url_for('admin_modules'))


@app.route('/admin/module/<int:module_id>/data')
@login_required
@role_required('admin')
def admin_module_data(module_id):
    module = Module.query.get_or_404(module_id)
    return {
        'id': module.id,
        'title': module.title,
        'description': module.description,
        'icon': getattr(module, 'icon', 'book')
    }


@app.route('/admin/module/<int:module_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def admin_edit_module(module_id):
    module = Module.query.get_or_404(module_id)

    title = request.form.get('title')
    description = request.form.get('description')
    icon = request.form.get('icon', 'book')

    if title:
        module.title = title
    module.description = description
    module.icon = icon

    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = file.filename.rsplit(
                '.', 1)[1].lower() if '.' in file.filename else ''

            if ext in allowed_extensions:
                if module.photo and module.photo != 'default_module.png':
                    old_filepath = os.path.join(app.config.get(
                        'UPLOAD_FOLDER', 'static/uploads'), 'modules', module.photo)
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except:
                            pass

                filename = f"module_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_folder = os.path.join(app.config.get(
                    'UPLOAD_FOLDER', 'static/uploads'), 'modules')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                module.photo = filename

    db.session.commit()
    flash(f'Модуль "{module.title}" успешно обновлен!', 'success')
    return redirect(url_for('admin_modules'))


@app.route('/admin/module/<int:module_id>/delete')
@login_required
@role_required('admin')
def admin_delete_module(module_id):
    module = Module.query.get_or_404(module_id)
    title = module.title

    db.session.delete(module)
    db.session.commit()

    flash(f'Модуль "{title}" успешно удален', 'success')
    return redirect(url_for('admin_modules'))


@app.route('/admin/module/<int:module_id>')
@login_required
@role_required('admin')
def admin_module_detail(module_id):
    module = Module.query.get_or_404(module_id)
    lessons = Lesson.query.filter_by(
        module_id=module.id).order_by(Lesson.id).all()

    total_tests = 0
    total_tasks = 0
    for lesson in lessons:
        total_tests += Test.query.filter_by(lesson_id=lesson.id).count()
        total_tasks += Task.query.filter_by(lesson_id=lesson.id).count()

    # НЕ передаем progress в админский шаблон!
    return render_template('admin/module_detail.html',
                           module=module,
                           lessons=lessons,
                           total_tests=total_tests,
                           total_tasks=total_tasks)


@app.route('/admin/reports')
@login_required
@role_required('admin')
def admin_reports():
    return render_template('admin/reports.html')


# ========== УПРАВЛЕНИЕ УРОКАМИ (АДМИН) ==========
@app.route('/admin/lesson/<int:lesson_id>/data')
@login_required
@role_required('admin')
def admin_lesson_data(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return {
        'id': lesson.id,
        'title': lesson.title,
        'content': lesson.content
    }


@app.route('/admin/module/<int:module_id>/create_lesson', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_lesson(module_id):
    module = Module.query.get_or_404(module_id)

    title = request.form.get('title')
    content = request.form.get('content')

    if not title:
        flash('Название урока обязательно', 'danger')
        return redirect(url_for('admin_module_detail', module_id=module_id))

    lesson = Lesson(
        module_id=module.id,
        title=title,
        content=content
    )

    db.session.add(lesson)
    db.session.commit()

    flash(f'Урок "{title}" успешно создан!', 'success')
    return redirect(url_for('admin_module_detail', module_id=module_id))


@app.route('/admin/lesson/<int:lesson_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def admin_edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    title = request.form.get('title')
    content = request.form.get('content')

    if title:
        lesson.title = title
    lesson.content = content

    db.session.commit()

    flash(f'Урок "{lesson.title}" успешно обновлен!', 'success')
    return redirect(url_for('admin_module_detail', module_id=lesson.module_id))


@app.route('/admin/lesson/<int:lesson_id>/delete')
@login_required
@role_required('admin')
def admin_delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    module_id = lesson.module_id
    title = lesson.title

    db.session.delete(lesson)
    db.session.commit()

    flash(f'Урок "{title}" успешно удален', 'success')
    return redirect(url_for('admin_module_detail', module_id=module_id))


@app.route('/admin/lesson/<int:lesson_id>')
@login_required
@role_required('admin')
def admin_lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    theory = Theory.query.filter_by(lesson_id=lesson.id).all()
    tests = Test.query.filter_by(lesson_id=lesson.id).all()
    tasks = Task.query.filter_by(lesson_id=lesson.id).all()

    return render_template('admin/lesson_detail.html',
                           lesson=lesson,
                           theory=theory,
                           tests=tests,
                           tasks=tasks)


# ========== УПРАВЛЕНИЕ ТЕОРИЕЙ ==========
@app.route('/admin/lesson/<int:lesson_id>/create_theory', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_theory(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    title = request.form.get('title')
    content = request.form.get('content')

    if not title:
        flash('Заголовок обязателен', 'danger')
        return redirect(url_for('admin_lesson_detail', lesson_id=lesson.id))

    theory = Theory(
        lesson_id=lesson.id,
        title=title,
        content=content,
        image='default_theory.png'
    )

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = file.filename.rsplit(
                '.', 1)[1].lower() if '.' in file.filename else ''

            if ext in allowed_extensions:
                filename = f"theory_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_folder = os.path.join(app.config.get(
                    'UPLOAD_FOLDER', 'static/uploads'), 'theories')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                theory.image = filename

    db.session.add(theory)
    db.session.commit()

    flash('Теоретический материал добавлен!', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson.id))


@app.route('/admin/theory/<int:theory_id>/data')
@login_required
@role_required('admin')
def admin_theory_data(theory_id):
    theory = Theory.query.get_or_404(theory_id)
    return {
        'id': theory.id,
        'title': theory.title,
        'content': theory.content,
        'image': theory.image
    }


@app.route('/admin/theory/<int:theory_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def admin_edit_theory(theory_id):
    theory = Theory.query.get_or_404(theory_id)

    theory.title = request.form.get('title')
    theory.content = request.form.get('content')

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = file.filename.rsplit(
                '.', 1)[1].lower() if '.' in file.filename else ''

            if ext in allowed_extensions:
                if theory.image and theory.image != 'default_theory.png':
                    old_filepath = os.path.join(app.config.get(
                        'UPLOAD_FOLDER', 'static/uploads'), 'theories', theory.image)
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except:
                            pass

                filename = f"theory_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_folder = os.path.join(app.config.get(
                    'UPLOAD_FOLDER', 'static/uploads'), 'theories')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                theory.image = filename

    db.session.commit()

    flash('Теоретический материал обновлен!', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=theory.lesson_id))


@app.route('/admin/theory/<int:theory_id>/delete')
@login_required
@role_required('admin')
def admin_delete_theory(theory_id):
    theory = Theory.query.get_or_404(theory_id)
    lesson_id = theory.lesson_id

    if theory.image and theory.image != 'default_theory.png':
        filepath = os.path.join(app.config.get(
            'UPLOAD_FOLDER', 'static/uploads'), 'theories', theory.image)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

    db.session.delete(theory)
    db.session.commit()

    flash('Теоретический материал удален', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson_id))


# ========== УПРАВЛЕНИЕ ТЕСТАМИ ==========
@app.route('/admin/lesson/<int:lesson_id>/create_test', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_test(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    options_text = request.form.get('options', '')
    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]

    test = Test(
        lesson_id=lesson.id,
        title=request.form.get('title'),
        text=request.form.get('text'),
        type=request.form.get('type', 'single'),
        answer=request.form.get('answer'),
        options=options
    )
    db.session.add(test)
    db.session.commit()
    flash('Тест создан', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson.id))


@app.route('/admin/test/<int:test_id>/delete')
@login_required
@role_required('admin')
def admin_delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    lesson_id = test.lesson_id
    db.session.delete(test)
    db.session.commit()
    flash('Тест удален', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson_id))


# ========== УПРАВЛЕНИЕ ЗАДАНИЯМИ ==========
@app.route('/admin/lesson/<int:lesson_id>/create_task', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_task(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    task = Task(
        lesson_id=lesson.id,
        title=request.form.get('title'),
        description=request.form.get('description'),
        link=request.form.get('link'),
        image=request.form.get('image')
    )
    db.session.add(task)
    db.session.commit()
    flash('Задание создано', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson.id))


@app.route('/admin/task/<int:task_id>/delete')
@login_required
@role_required('admin')
def admin_delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    lesson_id = task.lesson_id
    db.session.delete(task)
    db.session.commit()
    flash('Задание удалено', 'success')
    return redirect(url_for('admin_lesson_detail', lesson_id=lesson_id))


# ========== УПРАВЛЕНИЕ КОИНАМИ (УЧИТЕЛЬ) ==========

@app.route('/teacher/coins')
@login_required
@role_required('teacher')
def teacher_coins():
    """Страница начисления коинов ученикам"""
    # Получаем все группы учителя
    groups = Group.query.filter_by(created_by=current_user.id).all()

    # Собираем всех учеников из всех групп
    students = []
    for group in groups:
        for student in group.get_students():
            # Проверяем, не добавлен ли уже этот ученик
            existing = next(
                (s for s in students if s['user'].id == student.id), None)
            if not existing:
                # Получаем прогресс по модулю группы
                progress = ProgressModule.query.filter_by(
                    user_id=student.id,
                    module_id=group.module_id
                ).first()

                # Получаем количество выполненных заданий
                completed_tasks = 0
                if progress:
                    for lesson_data in progress.progress.get('lessons', {}).values():
                        for task_data in lesson_data.get('tasks', {}).values():
                            if task_data.get('completed', False):
                                completed_tasks += 1

                students.append({
                    'user': student,
                    'group': group,
                    'completed_tasks': completed_tasks,
                    'itcoins': student.itcoins
                })

    return render_template('teacher/coins.html', students=students, groups=groups)


@app.route('/teacher/coins/add', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_add_coins():
    """Начисление коинов ученику"""
    student_id = request.form.get('student_id')
    amount = request.form.get('amount')
    reason = request.form.get('reason', '')

    if not student_id or not amount:
        flash('Не указан ученик или сумма коинов', 'danger')
        return redirect(url_for('teacher_coins'))

    try:
        amount = int(amount)
        if amount <= 0:
            flash('Сумма коинов должна быть положительной', 'danger')
            return redirect(url_for('teacher_coins'))
        if amount > 1000:
            flash('Максимальная сумма для начисления - 1000 ITCoins', 'danger')
            return redirect(url_for('teacher_coins'))
    except ValueError:
        flash('Неверная сумма коинов', 'danger')
        return redirect(url_for('teacher_coins'))

    student = User.query.get_or_404(student_id)

    # Проверяем, что ученик действительно в группе учителя
    groups = Group.query.filter_by(created_by=current_user.id).all()
    student_in_group = False
    for group in groups:
        if group.has_student(student):
            student_in_group = True
            break

    if not student_in_group:
        flash('Этот ученик не состоит в ваших группах', 'danger')
        return redirect(url_for('teacher_coins'))

    # Начисляем коины
    student.itcoins += amount
    db.session.commit()

    flash(f'Начислено {amount} ITCoins ученику {student.username}!', 'success')

    return redirect(url_for('teacher_coins'))

# ========== УПРАВЛЕНИЕ ГРУППАМИ (УЧИТЕЛЬ/АДМИН) ==========


@app.route('/teacher/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    groups = Group.query.filter_by(created_by=current_user.id).all()

    # Добавляем количество учеников для каждой группы
    for group in groups:
        group.students_count = len(group.get_students())

    stats = {
        'groups_count': len(groups),
        'students_count': sum(g.students_count for g in groups),
        'modules_count': Module.query.count()
    }

    # Получаем все модули для выбора в модальном окне
    modules = Module.query.all()

    return render_template('teacher/dashboard.html', groups=groups, stats=stats, modules=modules)


@app.route('/teacher/groups')
@login_required
@role_required('teacher', 'admin')
def teacher_groups():
    if current_user.is_admin():
        groups = Group.query.all()
    else:
        groups = Group.query.filter_by(created_by=current_user.id).all()

    for group in groups:
        group.students_count = len(group.get_students())

    modules = Module.query.all()
    return render_template('teacher/groups.html', groups=groups, modules=modules)


@app.route('/teacher/group/create', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def teacher_create_group():
    title = request.form.get('title')
    module_id = request.form.get('module_id')
    date_str = request.form.get('date')

    if not title or not module_id or not date_str:
        flash('Заполните все поля', 'danger')
        return redirect(request.referrer or url_for('teacher_groups'))

    try:
        group = Group(
            title=title,
            module_id=int(module_id),
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            created_by=current_user.id
        )
        db.session.add(group)
        db.session.commit()

        chat = Chat(
            group_id=group.id,
            admin_id=current_user.id,
            title=f"Чат: {title}",
            users=[current_user.id]
        )
        db.session.add(chat)
        db.session.commit()

        flash(f'Группа "{title}" успешно создана!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании группы: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('teacher_groups'))


@app.route('/teacher/group/<int:group_id>')
@login_required
@role_required('teacher', 'admin')
def teacher_group_detail(group_id):
    import json
    group = Group.query.get_or_404(group_id)

    if not current_user.is_admin() and group.created_by != current_user.id:
        flash('У вас нет доступа к этой группе', 'danger')
        return redirect(url_for('teacher_groups'))

    module = Module.query.get(group.module_id)
    chat = group.get_chat()
    students = group.get_students()

    # Получаем все уроки модуля
    lessons = module.lessons_list if module else []

    # Собираем прогресс по каждому уроку
    lesson_progress = []

    for lesson in lessons:
        total_progress = 0
        student_count = 0

        for student in students:
            progress = ProgressModule.query.filter_by(
                user_id=student.id,
                module_id=group.module_id
            ).first()

            if progress:
                if isinstance(progress.progress, str):
                    progress_data = json.loads(progress.progress)
                else:
                    progress_data = progress.progress if progress.progress else {}

                lesson_data = progress_data.get(
                    'lessons', {}).get(str(lesson.id), {})

                # Вычисляем прогресс урока
                total_items = 0
                completed_items = 0

                # Теория
                total_items += 1
                if lesson_data.get('theory_viewed', False):
                    completed_items += 1

                # Тесты
                for test_data in lesson_data.get('tests', {}).values():
                    total_items += 1
                    if test_data.get('completed', False):
                        completed_items += 1

                # Задания
                for task_data in lesson_data.get('tasks', {}).values():
                    total_items += 1
                    if task_data.get('completed', False):
                        completed_items += 1

                if total_items > 0:
                    lesson_percent = int((completed_items / total_items) * 100)
                    total_progress += lesson_percent
                    student_count += 1

        if student_count > 0:
            avg_progress = int(total_progress / student_count)
        else:
            avg_progress = 0

        lesson_progress.append({
            'name': lesson.title[:30],
            'progress': avg_progress
        })

    # Вычисляем средний прогресс группы
    if students:
        total_student_progress = 0
        for student in students:
            progress = ProgressModule.query.filter_by(
                user_id=student.id,
                module_id=group.module_id
            ).first()
            if progress:
                if isinstance(progress.progress, str):
                    progress_data = json.loads(progress.progress)
                else:
                    progress_data = progress.progress if progress.progress else {}
                total_student_progress += progress_data.get('percentage', 0)
        avg_group_progress = int(total_student_progress / len(students))
    else:
        avg_group_progress = 0

    return render_template('teacher/group_detail.html',
                           group=group,
                           module=module,
                           students=students,
                           chat=chat,
                           lesson_progress=lesson_progress,
                           avg_group_progress=avg_group_progress)


# @app.route('/teacher/group/<int:group_id>/add_student', methods=['POST'])
# @login_required
# @role_required('teacher', 'admin')
# def teacher_add_student(group_id):
#     group = Group.query.get_or_404(group_id)

#     if not current_user.is_admin() and group.created_by != current_user.id:
#         flash('У вас нет прав для добавления учеников', 'danger')
#         return redirect(url_for('teacher_group_detail', group_id=group_id))

#     email = request.form.get('email')
#     if not email:
#         flash('Введите email ученика', 'warning')
#         return redirect(url_for('teacher_group_detail', group_id=group_id))

#     student = User.query.filter_by(email=email).first()
#     if not student:
#         flash(f'Пользователь с email {email} не найден', 'danger')
#         return redirect(url_for('teacher_group_detail', group_id=group_id))

#     if student.role != 'student':
#         flash(f'Пользователь {student.username} не является учеником', 'warning')
#         return redirect(url_for('teacher_group_detail', group_id=group_id))

#     if group.has_student(student):
#         flash(f'Ученик {student.username} уже состоит в этой группе', 'warning')
#         return redirect(url_for('teacher_group_detail', group_id=group_id))

#     if group.add_student(student):
#         chat = group.get_chat()
#         if chat and student.id not in chat.users:
#             chat.users.append(student.id)
#             db.session.commit()
#         flash(f'Ученик {student.username} успешно добавлен в группу!', 'success')
#     else:
#         flash('Ошибка при добавлении ученика', 'danger')

#     return redirect(url_for('teacher_group_detail', group_id=group_id))


@app.route('/teacher/group/<int:group_id>/add_student', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def teacher_add_student(group_id):
    import json

    group = Group.query.get_or_404(group_id)

    if not current_user.is_admin() and group.created_by != current_user.id:
        flash('У вас нет прав для добавления учеников', 'danger')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    email = request.form.get('email')
    if not email:
        flash('Введите email ученика', 'warning')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    student = User.query.filter_by(email=email).first()
    if not student:
        flash(f'Пользователь с email {email} не найден', 'danger')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    if student.role != 'student':
        flash(
            f'Пользователь {student.username} не является учеником', 'warning')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    if group.has_student(student):
        flash(
            f'Ученик {student.username} уже состоит в этой группе', 'warning')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    # Добавляем ученика в группу
    if group.add_student(student):
        # Добавляем ученика в чат
        chat = group.get_chat()
        if chat and student.id not in chat.users:
            chat.users.append(student.id)
            db.session.commit()

        # ========== СОЗДАЕМ ПРОГРЕСС ДЛЯ МОДУЛЯ ==========
        module = Module.query.get(group.module_id)
        if module:
            # Проверяем, есть ли уже прогресс
            existing_progress = ProgressModule.query.filter_by(
                user_id=student.id,
                module_id=module.id
            ).first()

            if not existing_progress:
                # Создаем полную структуру прогресса
                progress_data = {
                    'percentage': 0,
                    'completed_lessons': [],
                    'current_lesson': None,
                    'lessons': {}
                }

                # Добавляем все уроки модуля
                for lesson in module.lessons_list:
                    lesson_data = {
                        'title': lesson.title,
                        'completed': False,
                        'started': False,
                        'tests': {},
                        'tasks': {},
                        'theory_viewed': False
                    }

                    # Добавляем все тесты урока
                    for test in lesson.tests_list:
                        lesson_data['tests'][str(test.id)] = {
                            'title': test.title,
                            'completed': False,
                            'score': 0,
                            'attempts': 0,
                            'last_answer': None,
                            'is_correct': False
                        }

                    # Добавляем все задания урока
                    for task in lesson.tasks_list:
                        lesson_data['tasks'][str(task.id)] = {
                            'title': task.title,
                            'completed': False,
                            'submitted': False,
                            'score': 0
                        }

                    progress_data['lessons'][str(lesson.id)] = lesson_data

                new_progress = ProgressModule(
                    user_id=student.id,
                    module_id=module.id,
                    progress=progress_data
                )
                db.session.add(new_progress)
                db.session.commit()
                print(
                    f"✅ Создан прогресс для ученика {student.username} по модулю {module.title}")
                print(f"   Уроков: {len(progress_data['lessons'])}")
                for lesson_id, lesson in progress_data['lessons'].items():
                    print(
                        f"   - Урок {lesson_id}: тестов={len(lesson['tests'])}, заданий={len(lesson['tasks'])}")
            else:
                print(
                    f"⚠️ Прогресс для ученика {student.username} по модулю {module.title} уже существует")

        flash(
            f'Ученик {student.username} успешно добавлен в группу!', 'success')
    else:
        flash('Ошибка при добавлении ученика', 'danger')

    return redirect(url_for('teacher_group_detail', group_id=group_id))


@app.route('/teacher/group/<int:group_id>/remove_student/<int:student_id>', methods=['POST'])
@login_required
@role_required('teacher', 'admin')
def teacher_remove_student(group_id, student_id):
    group = Group.query.get_or_404(group_id)

    if not current_user.is_admin() and group.created_by != current_user.id:
        flash('У вас нет прав для удаления учеников', 'danger')
        return redirect(url_for('teacher_group_detail', group_id=group_id))

    student = User.query.get_or_404(student_id)

    if group.remove_student(student):
        chat = group.get_chat()
        if chat and student.id in chat.users:
            chat.users.remove(student.id)
            db.session.commit()
        flash(f'Ученик {student.username} удален из группы', 'success')
    else:
        flash(f'Ученик {student.username} не найден в этой группе', 'warning')

    return redirect(url_for('teacher_group_detail', group_id=group_id))


@app.route('/teacher/group/<int:group_id>/delete')
@login_required
@role_required('teacher', 'admin')
def teacher_delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    if not current_user.is_admin() and group.created_by != current_user.id:
        flash('У вас нет прав для удаления группы', 'danger')
        return redirect(url_for('teacher_groups'))

    title = group.title

    GroupStudent.query.filter_by(group_id=group_id).delete()

    chat = group.get_chat()
    if chat:
        db.session.delete(chat)

    db.session.delete(group)
    db.session.commit()

    flash(f'Группа "{title}" успешно удалена', 'success')
    return redirect(url_for('teacher_groups'))


# ============================================================
# УЧЕНИК МАРШРУТЫ
# ============================================================
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('У вас нет доступа к панели ученика', 'danger')
        return redirect(url_for('dashboard'))

    modules = Module.query.all()
    total_lessons = Lesson.query.count()
    completed_lessons = 0

    for module in modules:
        progress = ProgressModule.query.filter_by(
            user_id=current_user.id,
            module_id=module.id
        ).first()

        if progress and progress.progress:
            module.progress = progress.progress.get('percentage', 0)
            if module.progress >= 100:
                completed_lessons += 1
        else:
            module.progress = 0

    overall_progress = (completed_lessons / total_lessons *
                        100) if total_lessons > 0 else 0

    return render_template('student/dashboard.html',
                           modules=modules,
                           overall_progress=int(overall_progress),
                           completed_lessons=completed_lessons,
                           total_lessons=total_lessons)


@app.route('/student/module/<int:module_id>')
@login_required
def student_module(module_id):
    import json

    module = Module.query.get_or_404(module_id)
    lessons = Lesson.query.filter_by(module_id=module.id).all()

    progress = ProgressModule.query.filter_by(
        user_id=current_user.id,
        module_id=module_id
    ).first()

    # Если прогресса нет — создаем
    if not progress:
        progress = ProgressModule(
            user_id=current_user.id,
            module_id=module_id,
            progress={
                'percentage': 0,
                'completed_lessons': [],
                'current_lesson': None,
                'lessons': {}
            }
        )
        db.session.add(progress)

        # Инициализируем все уроки модуля
        for lesson in lessons:
            lesson_key = str(lesson.id)
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

            progress.progress['lessons'][lesson_key] = lesson_data

        db.session.add(progress)
        db.session.commit()
        print(
            f"✅ Создан прогресс для модуля {module.title} для {current_user.username}")
    else:
        # Преобразуем строку в словарь
        if isinstance(progress.progress, str):
            try:
                progress.progress = json.loads(progress.progress)
            except:
                progress.progress = {}

        if not isinstance(progress.progress, dict):
            progress.progress = {}

        # Проверяем и добавляем ключи
        need_save = False

        if 'lessons' not in progress.progress:
            progress.progress['lessons'] = {}
            need_save = True

        if 'percentage' not in progress.progress:
            progress.progress['percentage'] = 0
            need_save = True

        if 'completed_lessons' not in progress.progress:
            progress.progress['completed_lessons'] = []
            need_save = True

        if 'current_lesson' not in progress.progress:
            progress.progress['current_lesson'] = None
            need_save = True

        # Проверяем все уроки
        for lesson in lessons:
            lesson_key = str(lesson.id)
            if lesson_key not in progress.progress.get('lessons', {}):
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

                progress.progress['lessons'][lesson_key] = lesson_data
                need_save = True
                print(
                    f"✅ Добавлен урок {lesson.title} для {current_user.username}")

        if need_save:
            db.session.commit()

    return render_template('student/module_detail.html',
                           module=module,
                           lessons=lessons,
                           progress=progress)


@app.route('/student/lesson/<int:lesson_id>')
@login_required
def student_lesson(lesson_id):
    import json

    lesson = Lesson.query.get_or_404(lesson_id)

    progress = ProgressModule.query.filter_by(
        user_id=current_user.id,
        module_id=lesson.module_id
    ).first()

    # Если прогресса нет — создаем
    if not progress:
        module = Module.query.get(lesson.module_id)
        progress = ProgressModule(
            user_id=current_user.id,
            module_id=lesson.module_id,
            progress={
                'percentage': 0,
                'completed_lessons': [],
                'current_lesson': None,
                'lessons': {}
            }
        )
        db.session.add(progress)
        db.session.commit()
        print(f"✅ Создан новый прогресс для {current_user.username}")

    # Преобразуем строку в словарь
    if isinstance(progress.progress, str):
        try:
            progress.progress = json.loads(progress.progress)
        except:
            progress.progress = {}

    # Если не словарь — создаем новый
    if not isinstance(progress.progress, dict):
        progress.progress = {}

    # ========== ГЛАВНАЯ ПРОВЕРКА СТРУКТУРЫ ==========
    need_save = False

    # Проверяем lessons
    if 'lessons' not in progress.progress:
        progress.progress['lessons'] = {}
        need_save = True
        print(f"⚠️ Добавлен ключ 'lessons'")
    elif progress.progress['lessons'] is None:
        progress.progress['lessons'] = {}
        need_save = True
        print(f"⚠️ Исправлен None в 'lessons'")

    # Проверяем другие ключи
    if 'percentage' not in progress.progress:
        progress.progress['percentage'] = 0
        need_save = True

    if 'completed_lessons' not in progress.progress:
        progress.progress['completed_lessons'] = []
        need_save = True

    if 'current_lesson' not in progress.progress:
        progress.progress['current_lesson'] = None
        need_save = True

    if need_save:
        db.session.commit()
        print(f"✅ Структура прогресса восстановлена")

    # ========== ПРОВЕРКА НАЛИЧИЯ УРОКА ==========
    lesson_key = str(lesson.id)

    # Убеждаемся, что lessons — это словарь
    if not isinstance(progress.progress.get('lessons'), dict):
        progress.progress['lessons'] = {}
        db.session.commit()

    # Проверяем наличие урока
    if lesson_key not in progress.progress['lessons']:
        # Создаем структуру урока
        lesson_data = {
            'title': lesson.title,
            'completed': False,
            'started': False,
            'tests': {},
            'tasks': {},
            'theory_viewed': False
        }

        # Добавляем все тесты урока
        for test in lesson.tests_list:
            lesson_data['tests'][str(test.id)] = {
                'title': test.title,
                'completed': False,
                'score': 0,
                'attempts': 0,
                'last_answer': None,
                'is_correct': False
            }

        # Добавляем все задания урока
        for task in lesson.tasks_list:
            lesson_data['tasks'][str(task.id)] = {
                'title': task.title,
                'completed': False,
                'submitted': False,
                'score': 0
            }

        progress.progress['lessons'][lesson_key] = lesson_data
        db.session.commit()
        print(f"✅ Создан урок {lesson.title} в прогрессе")

    # Теперь безопасно получаем данные урока
    lesson_data = progress.progress['lessons'][lesson_key]

    # Отмечаем, что урок начат
    if not lesson_data.get('started', False):
        lesson_data['started'] = True
        db.session.commit()
        print(f"✅ Урок {lesson.title} отмечен как начатый")

    theory = Theory.query.filter_by(lesson_id=lesson.id).all()
    tests = Test.query.filter_by(lesson_id=lesson.id).all()
    tasks = Task.query.filter_by(lesson_id=lesson.id).all()

    return render_template('student/lesson.html',
                           lesson=lesson,
                           theory=theory,
                           tests=tests,
                           tasks=tasks,
                           progress=progress)


@app.route('/student/test/<int:test_id>', methods=['POST'])
@login_required
def student_test(test_id):
    import copy

    test = Test.query.get_or_404(test_id)
    lesson = Lesson.query.get(test.lesson_id)

    if request.method == 'POST':
        user_answer = request.form.get('answer', '')

        progress = ProgressModule.query.filter_by(
            user_id=current_user.id,
            module_id=lesson.module_id
        ).first()

        if not progress:
            flash('Прогресс не найден', 'danger')
            return redirect(url_for('student_lesson', lesson_id=lesson.id))

        # Делаем копию и обновляем
        data = copy.deepcopy(progress.progress)

        lesson_key = str(lesson.id)
        test_key = str(test.id)

        if lesson_key not in data.get('lessons', {}):
            flash('Урок не найден', 'danger')
            return redirect(url_for('student_lesson', lesson_id=lesson.id))

        if test_key not in data['lessons'][lesson_key].get('tests', {}):
            flash('Тест не найден', 'danger')
            return redirect(url_for('student_lesson', lesson_id=lesson.id))

        test_info = data['lessons'][lesson_key]['tests'][test_key]

        if test_info.get('completed', False):
            flash('Этот тест уже пройден!', 'info')
            return redirect(url_for('student_lesson', lesson_id=lesson.id))

        # Проверка ответа
        if test.type == 'single':
            is_correct = user_answer.strip() == test.answer.strip()
        elif test.type == 'multiple':
            user_answers = set(a.strip() for a in user_answer.split(','))
            correct_answers = set(a.strip() for a in test.answer.split(','))
            is_correct = user_answers == correct_answers
        else:
            is_correct = user_answer.lower().strip() == test.answer.lower().strip()

        # Обновляем
        test_info['completed'] = True
        test_info['score'] = 100
        test_info['attempts'] = test_info.get('attempts', 0) + 1
        test_info['last_answer'] = user_answer
        test_info['is_correct'] = is_correct

        # Присваиваем обратно
        progress.progress = data

        if is_correct:
            current_user.itcoins += 10
            flash(f'✅ Правильно! Вы получили 10 ITCoins!', 'success')
        else:
            flash(f'❌ Неправильно. Правильный ответ: {test.answer}', 'warning')

        db.session.commit()

        return redirect(url_for('student_lesson', lesson_id=lesson.id))

    return render_template('student/test.html', test=test)

# маршрут для отметки теории


@app.route('/student/lesson/<int:lesson_id>/theory_viewed', methods=['POST'])
@login_required
def mark_theory_viewed(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    progress = ProgressModule.query.filter_by(
        user_id=current_user.id,
        module_id=lesson.module_id
    ).first()

    if not progress:
        module = Module.query.get(lesson.module_id)
        progress = ProgressModule(
            user_id=current_user.id,
            module_id=lesson.module_id
        )
        progress.init_progress(module)
        db.session.add(progress)

    if str(lesson.id) not in progress.progress.get('lessons', {}):
        progress.progress['lessons'][str(lesson.id)] = {
            'title': lesson.title,
            'completed': False,
            'started': True,
            'tests': {},
            'tasks': {},
            'theory_viewed': False
        }

    progress.progress['lessons'][str(lesson.id)]['theory_viewed'] = True

    # Проверяем, можно ли завершить урок
    lesson_tests = progress.progress['lessons'][str(
        lesson.id)].get('tests', {})
    all_tests_completed = all(t.get('completed', False)
                              for t in lesson_tests.values())
    all_tasks_completed = all(t.get('completed', False)
                              for t in progress.progress['lessons'][str(lesson.id)].get('tasks', {}).values())

    if all_tests_completed and all_tasks_completed:
        progress.progress['lessons'][str(lesson.id)]['completed'] = True
        if str(lesson.id) not in progress.progress.get('completed_lessons', []):
            progress.progress['completed_lessons'].append(str(lesson.id))
        progress.update_percentage()
        flash('🎉 Поздравляем! Вы завершили урок!', 'success')

    db.session.commit()

    return {'success': True}

# маршрут для завершения задания


@app.route('/student/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    lesson = Lesson.query.get(task.lesson_id)

    progress = ProgressModule.query.filter_by(
        user_id=current_user.id,
        module_id=lesson.module_id
    ).first()

    if not progress:
        return {'success': False}, 400

    if str(lesson.id) not in progress.progress.get('lessons', {}):
        progress.progress['lessons'][str(lesson.id)] = {
            'title': lesson.title,
            'completed': False,
            'started': True,
            'tests': {},
            'tasks': {},
            'theory_viewed': False
        }

    if str(task.id) not in progress.progress['lessons'][str(lesson.id)].get('tasks', {}):
        progress.progress['lessons'][str(lesson.id)]['tasks'][str(task.id)] = {
            'title': task.title,
            'completed': False,
            'submitted': False,
            'score': 0
        }

    task_info = progress.progress['lessons'][str(
        lesson.id)]['tasks'][str(task.id)]

    if not task_info.get('completed', False):
        task_info['completed'] = True
        task_info['submitted'] = True

        # Проверяем, можно ли завершить урок
        lesson_tests = progress.progress['lessons'][str(
            lesson.id)].get('tests', {})
        all_tests_completed = all(t.get('completed', False)
                                  for t in lesson_tests.values())
        theory_viewed = progress.progress['lessons'][str(
            lesson.id)].get('theory_viewed', False)
        all_tasks_completed = all(t.get('completed', False) for t in progress.progress['lessons'][str(
            lesson.id)].get('tasks', {}).values())

        if all_tests_completed and theory_viewed and all_tasks_completed:
            progress.progress['lessons'][str(lesson.id)]['completed'] = True
            if str(lesson.id) not in progress.progress.get('completed_lessons', []):
                progress.progress['completed_lessons'].append(str(lesson.id))
            progress.update_percentage()
            flash('🎉 Поздравляем! Вы завершили урок!', 'success')

        db.session.commit()
        return {'success': True}

    return {'success': False}, 400

# ============================================================
# ПРОГРЕСС (ТЕСТ) МАРШРУТЫ
# ============================================================


@app.route('/debug/progress')
@login_required
def debug_progress():
    """Отладочная страница для просмотра прогресса"""
    progress = ProgressModule.query.filter_by(
        user_id=current_user.id,
        module_id=1  # ID модуля, который проверяете
    ).first()

    if progress:
        return f"""
        <h3>Прогресс пользователя {current_user.username}</h3>
        <pre>{progress.progress}</pre>
        <p>ITCoins: {current_user.itcoins}</p>
        """
    else:
        return "Прогресс не найден"

# ============================================================
# РОДИТЕЛЬ МАРШРУТЫ
# ============================================================
# ============================================================
# РОДИТЕЛЬ МАРШРУТЫ
# ============================================================


@app.route('/parent/dashboard')
@login_required
@role_required('parent')
def parent_dashboard():
    import json

    children_relations = Parent.query.filter_by(
        id_parent=current_user.id).all()
    children_data = []

    for rel in children_relations:
        child = User.query.get(rel.id_child)
        if child:
            modules_progress = []
            total_percent = 0
            total_completed_tests = 0
            total_tests_count = 0

            for module in Module.query.all():
                progress = ProgressModule.query.filter_by(
                    user_id=child.id,
                    module_id=module.id
                ).first()

                module_percent = 0
                module_completed_tests = 0
                module_tests_count = 0

                if progress:
                    # Получаем данные
                    if isinstance(progress.progress, str):
                        try:
                            progress_data = json.loads(progress.progress)
                        except:
                            progress_data = {}
                    else:
                        progress_data = progress.progress if progress.progress else {}

                    # Считаем пройденные тесты
                    for lesson_data in progress_data.get('lessons', {}).values():
                        for test_data in lesson_data.get('tests', {}).values():
                            module_tests_count += 1
                            if test_data.get('completed', False):
                                module_completed_tests += 1
                                total_completed_tests += 1
                                total_tests_count += 1
                            else:
                                total_tests_count += 1

                    # Прогресс модуля = процент пройденных тестов
                    if module_tests_count > 0:
                        module_percent = int(
                            (module_completed_tests / module_tests_count) * 100)
                    total_percent += module_percent

                modules_progress.append({
                    'module': module,
                    'progress': module_percent
                })

            module_count = Module.query.count()
            avg_progress = int(
                total_percent / module_count) if module_count > 0 else 0

            children_data.append({
                'child': child,
                'total_progress': avg_progress,
                'completed_lessons': total_completed_tests,  # показываем пройденные тесты
                'completed_tests': total_completed_tests,
                'total_tests': total_tests_count,
                'itcoins': child.itcoins,
                'streak_days': getattr(child, 'streak_days', 0),
                'modules_progress': modules_progress
            })

    return render_template('parent/dashboard.html', children_data=children_data)


@app.route('/parent/child/<int:child_id>')
@login_required
@role_required('parent')
def parent_child_progress(child_id):
    import json

    # Проверяем, что ребенок принадлежит родителю
    relation = Parent.query.filter_by(
        id_parent=current_user.id, id_child=child_id).first()
    if not relation:
        flash('У вас нет доступа к этому ребенку', 'danger')
        return redirect(url_for('parent_dashboard'))

    child = User.query.get_or_404(child_id)

    # Получаем прогресс по модулям
    modules_progress = []
    total_lessons = 0
    completed_lessons = 0
    total_tests = 0
    completed_tests = 0
    total_tasks = 0
    completed_tasks = 0

    for module in Module.query.all():
        progress = ProgressModule.query.filter_by(
            user_id=child.id,
            module_id=module.id
        ).first()

        module_completed_tests = 0
        module_total_tests = 0
        module_completed_tasks = 0
        module_total_tasks = 0
        module_completed_lessons = 0
        module_total_lessons = len(module.lessons_list)
        module_percent = 0

        if progress:
            # Преобразуем строку в словарь
            if isinstance(progress.progress, str):
                try:
                    progress_data = json.loads(progress.progress)
                except:
                    progress_data = {}
            else:
                progress_data = progress.progress if progress.progress else {}

            # Считаем пройденные тесты
            for lesson_data in progress_data.get('lessons', {}).values():
                for test_data in lesson_data.get('tests', {}).values():
                    module_total_tests += 1
                    total_tests += 1
                    if test_data.get('completed', False):
                        module_completed_tests += 1
                        completed_tests += 1

                for task_data in lesson_data.get('tasks', {}).values():
                    module_total_tasks += 1
                    total_tasks += 1
                    if task_data.get('completed', False):
                        module_completed_tasks += 1
                        completed_tasks += 1

            # Считаем пройденные уроки
            module_completed_lessons = len(
                progress_data.get('completed_lessons', []))
            completed_lessons += module_completed_lessons
            total_lessons += module_total_lessons

            # Прогресс модуля = процент пройденных тестов
            if module_total_tests > 0:
                module_percent = int(
                    (module_completed_tests / module_total_tests) * 100)

            modules_progress.append({
                'module': module,
                'progress': module_percent,
                'completed_lessons': module_completed_lessons,
                'total_lessons': module_total_lessons,
                'completed_tests': module_completed_tests,
                'total_tests': module_total_tests,
                'completed_tasks': module_completed_tasks,
                'total_tasks': module_total_tasks,
                'progress_data': progress_data
            })
        else:
            modules_progress.append({
                'module': module,
                'progress': 0,
                'completed_lessons': 0,
                'total_lessons': module_total_lessons,
                'completed_tests': 0,
                'total_tests': 0,
                'completed_tasks': 0,
                'total_tasks': 0,
                'progress_data': {}
            })

    # Получаем результаты тестов (уникальные, без дубликатов)
    test_results = TestResult.query.filter_by(
        user_id=child.id).order_by(TestResult.date.desc()).all()

    # Удаляем дубликаты (оставляем последнюю попытку для каждого теста)
    unique_results = {}
    for result in test_results:
        key = result.test_id
        if key not in unique_results:
            unique_results[key] = result

    unique_results_list = list(unique_results.values())

    # Для каждого результата подгружаем название теста и урока
    for result in unique_results_list:
        result.test = Test.query.get(result.test_id)
        if result.test:
            result.lesson = Lesson.query.get(result.test.lesson_id)

    return render_template('parent/child_progress.html',
                           child=child,
                           modules_progress=modules_progress,
                           test_results=unique_results_list,
                           total_lessons=total_lessons,
                           completed_lessons=completed_lessons,
                           total_tests=total_tests,
                           completed_tests=completed_tests,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks)


@app.route('/parent/child/<int:child_id>/send_report', methods=['POST'])
@login_required
@role_required('parent')
def parent_send_report(child_id):
    """Отправка отчета о прогрессе на email"""
    relation = Parent.query.filter_by(
        id_parent=current_user.id, id_child=child_id).first()
    if not relation:
        return {'success': False}, 403

    child = User.query.get_or_404(child_id)

    # Здесь можно отправить email с отчетом
    # Пока просто возвращаем успех
    print(f"Отчет отправлен для {child.username} на {current_user.email}")

    return {'success': True}


# ============================================================
# ЧАТ МАРШРУТЫ
# ============================================================
@app.route('/chat')
@login_required
def chat_index():
    """Список чатов пользователя"""
    user_id = current_user.id
    user_id_str = str(user_id)

    # Ищем чаты, где users содержит ID пользователя
    # SQLite: используем LIKE для поиска в JSON
    chats = Chat.query.filter(
        Chat.users.cast(db.String).like(f'%{user_id_str}%')
    ).all()

    chat_data = []
    for chat in chats:
        group = Group.query.get(chat.group_id) if chat.group_id else None
        chat_data.append({
            'chat': chat,
            'group': group,
            'unread_count': 0
        })

    return render_template('chat/index.html', chats=chat_data)


@app.route('/chat/<int:chat_id>')
@login_required
def chat_room(chat_id):
    chat = Chat.query.get_or_404(chat_id)

    if current_user.id not in chat.users:
        flash('У вас нет доступа к этому чату', 'danger')
        return redirect(url_for('chat_index'))

    messages = Message.query.filter_by(
        chat_id=chat_id).order_by(Message.datetime).all()
    group = Group.query.get(chat.group_id) if chat.group_id else None

    return render_template('chat/room.html', chat=chat, messages=messages, group=group)


@app.route('/chat/<int:chat_id>/send', methods=['POST'])
@login_required
def chat_send(chat_id):
    chat = Chat.query.get_or_404(chat_id)

    if current_user.id not in chat.users:
        flash('У вас нет доступа к этому чату', 'danger')
        return redirect(url_for('chat_index'))

    message_text = request.form.get('message')
    if message_text and message_text.strip():
        message = Message(
            user_id=current_user.id,
            chat_id=chat_id,
            text=message_text.strip(),
            datetime=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()

    return redirect(url_for('chat_room', chat_id=chat_id))


# ============================================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================================
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


# ============================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ База данных инициализирована")

        create_default_users()
        create_demo_content()

    app.run(debug=True)
