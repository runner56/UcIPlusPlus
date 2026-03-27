# check_real_progress.py
from app import app, db
from models import User, Parent, ProgressModule, Module
import json

with app.app_context():
    parent = User.query.filter_by(username='parent').first()
    if not parent:
        print("Родитель не найден")
        exit()
    
    print(f"Родитель: {parent.username}\n")
    
    children = Parent.query.filter_by(id_parent=parent.id).all()
    
    for rel in children:
        child = User.query.get(rel.id_child)
        print(f"{'='*60}")
        print(f"Ребенок: {child.username} (ID: {child.id})")
        print(f"ITCoins: {child.itcoins}")
        
        for module in Module.query.all():
            progress = ProgressModule.query.filter_by(
                user_id=child.id,
                module_id=module.id
            ).first()
            
            print(f"\n  Модуль: {module.title}")
            
            if progress:
                if isinstance(progress.progress, str):
                    data = json.loads(progress.progress)
                else:
                    data = progress.progress if progress.progress else {}
                
                print(f"    Полные данные прогресса:")
                print(f"    {json.dumps(data, ensure_ascii=False, indent=6)}")
                
                percent = data.get('percentage', 0)
                completed_lessons = data.get('completed_lessons', [])
                
                print(f"\n    Процент: {percent}%")
                print(f"    Пройденные уроки: {completed_lessons}")
                
                # Проверяем каждый урок
                for lesson_id, lesson_data in data.get('lessons', {}).items():
                    print(f"\n    Урок {lesson_id}: {lesson_data.get('title', '')}")
                    print(f"      completed: {lesson_data.get('completed', False)}")
                    print(f"      started: {lesson_data.get('started', False)}")
                    print(f"      theory_viewed: {lesson_data.get('theory_viewed', False)}")
                    
                    # Тесты
                    for test_id, test_data in lesson_data.get('tests', {}).items():
                        print(f"      Тест {test_id}: completed={test_data.get('completed', False)}, is_correct={test_data.get('is_correct', False)}")
                    
                    # Задания
                    for task_id, task_data in lesson_data.get('tasks', {}).items():
                        print(f"      Задание {task_id}: completed={task_data.get('completed', False)}")
            else:
                print(f"    ❌ Нет прогресса")
        
        print()