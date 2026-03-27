# fix_all_progress.py
from app import app, db
from models import ProgressModule, Module, User
import json

with app.app_context():
    progresses = ProgressModule.query.all()
    fixed_count = 0
    
    for progress in progresses:
        user = User.query.get(progress.user_id)
        module = Module.query.get(progress.module_id)
        
        if not module:
            continue
        
        # Преобразуем
        if isinstance(progress.progress, str):
            try:
                data = json.loads(progress.progress)
            except:
                data = {}
        else:
            data = progress.progress if progress.progress else {}
        
        if not isinstance(data, dict):
            data = {}
        
        changed = False
        
        # Исправляем lessons
        if 'lessons' not in data:
            data['lessons'] = {}
            changed = True
        elif data['lessons'] is None:
            data['lessons'] = {}
            changed = True
        
        # Добавляем другие ключи
        if 'percentage' not in data:
            data['percentage'] = 0
            changed = True
        
        if 'completed_lessons' not in data:
            data['completed_lessons'] = []
            changed = True
        
        if 'current_lesson' not in data:
            data['current_lesson'] = None
            changed = True
        
        # Добавляем все уроки модуля
        for lesson in module.lessons_list:
            lesson_key = str(lesson.id)
            if lesson_key not in data['lessons']:
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
                
                data['lessons'][lesson_key] = lesson_data
                changed = True
                print(f"  Добавлен урок {lesson.title} для {user.username}")
        
        if changed:
            progress.progress = data
            db.session.commit()
            fixed_count += 1
            print(f"✅ Исправлен прогресс для {user.username} (модуль {module.title})")
    
    print(f"\nВсего исправлено: {fixed_count} записей")