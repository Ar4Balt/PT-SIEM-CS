import json
import random
import os
import time
import threading
import sys
from datetime import datetime
import urllib.request
import urllib.error
import hashlib
import json
import os
from pathlib import Path
import shutil

# Файлы
COURSES_DIR = "courses"
RESULTS_FILE = "results.txt"

# Настройки экзамена
EXAM_TIME = 3600          # 1 час = 3600 секунд
EXAM_QUESTIONS = 45       # количество вопросов в экзамене
EXAM_PASS_SCORE = 34      # порог сдачи

stop_timer = False
time_string = ""

# GitHub-репозиторий (ветка main)
GITHUB_API = "https://api.github.com/repos/Ar4Balt/PT-SIEM-CS/contents/"
GITHUB_RAW = "https://raw.githubusercontent.com/Ar4Balt/PT-SIEM-CS/main/"

# файлы/папки, которые никогда не трогаем
IGNORE_PATHS = {
    ".git", ".github",           # Git и GitHub
    ".idea", ".vscode",          # IDE (PyCharm, VSCode)
    ".venv", "venv", "env",      # виртуальные окружения
    "__pycache__", ".mypy_cache", ".pytest_cache",  # кэши
    ".DS_Store", "Thumbs.db",    # системные файлы (macOS, Windows)
    "results.txt"                # результаты сдачи
}

FILES_TO_CHECK = [
    "quiz.py",
    "README.md"
]

def md5(content: str) -> str:
    """Вычисляет md5-хэш строки"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def fetch_github_files(path=""):
    """Возвращает список файлов и папок с GitHub API"""
    url = GITHUB_API + path
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"⚠️ Не удалось получить список файлов {path}: {e}")
        return []

def download_file(url, local_path):
    """Скачивает файл с GitHub"""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode("utf-8")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"⬆️ Обновлён: {local_path}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {url}: {e}")

def check_and_update_file(file):
    """Сравнивает локальный и удалённый файл, при различии обновляет"""
    url = GITHUB_RAW + file
    local_path = Path(file)

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            remote_content = response.read().decode("utf-8")
    except urllib.error.URLError:
        print("⚠️ Не удалось подключиться к GitHub. Работаем офлайн.")
        return

    local_content = ""
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            local_content = f.read()

    if md5(local_content) != md5(remote_content):
        download_file(url, local_path)
    else:
        print(f"✔️ Актуален: {file}")

def update_courses():
    """Скачивает и обновляет все файлы из папки courses/"""
    try:
        with urllib.request.urlopen(GITHUB_API + "courses", timeout=5) as response:
            files = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError:
        print("⚠️ Не удалось проверить курсы. Работаем офлайн.")
        return

    for item in files:
        if item["type"] == "dir":
            # заходим внутрь подпапок
            with urllib.request.urlopen(item["url"], timeout=5) as response:
                subfiles = json.loads(response.read().decode("utf-8"))
            for sf in subfiles:
                if sf["type"] == "file":
                    rel_path = f"courses/{Path(sf['path']).name}"
                    url = sf["download_url"]
                    local_path = Path(sf["path"])
                    try:
                        with urllib.request.urlopen(url, timeout=5) as r:
                            remote_content = r.read().decode("utf-8")
                        local_content = ""
                        if local_path.exists():
                            with open(local_path, "r", encoding="utf-8") as f:
                                local_content = f.read()
                        if md5(local_content) != md5(remote_content):
                            download_file(url, local_path)
                        else:
                            print(f"✔️ Актуален: {local_path}")
                    except Exception as e:
                        print(f"⚠️ Ошибка загрузки {url}: {e}")

def sync_with_github(path=""):
    """Синхронизирует локальные файлы с GitHub"""
    items = fetch_github_files(path)
    if not items:
        return

    remote_files = []
    for item in items:
        rel_path = os.path.join(path, item["name"])
        local_path = Path(rel_path)

        if item["type"] == "file":
            remote_files.append(str(local_path))
            try:
                with urllib.request.urlopen(item["download_url"], timeout=5) as r:
                    remote_content = r.read().decode("utf-8")
                local_content = ""
                if local_path.exists():
                    with open(local_path, "r", encoding="utf-8") as f:
                        local_content = f.read()
                if md5(local_content) != md5(remote_content):
                    download_file(item["download_url"], local_path)
                else:
                    print(f"✔️ Актуален: {local_path}")
            except Exception as e:
                print(f"⚠️ Ошибка проверки {rel_path}: {e}")

        elif item["type"] == "dir":
            sync_with_github(rel_path)
            remote_files.append(str(local_path))

    # удаляем лишние локальные файлы/папки
    local_dir = Path(path) if path else Path(".")
    if local_dir.exists():
        for child in local_dir.iterdir():
            if child.name in IGNORE_PATHS:  # игнорируем служебные файлы/папки
                continue
            if str(child) not in remote_files:
                if child.is_file():
                    child.unlink()
                    print(f"🗑️ Удалён лишний файл: {child}")
                elif child.is_dir():
                    shutil.rmtree(child)
                    print(f"🗑️ Удалена лишняя папка: {child}")

def check_updates():
    """Главная функция синхронизации"""
    print("🔍 Проверка обновлений...")

    sync_with_github("")    # синхронизируем всё с корня репозитория

    # основные файлы
    for file in FILES_TO_CHECK:
        check_and_update_file(file)

    # курсы
    update_courses()

def list_courses():
    """Сканируем папку с курсами"""
    if not os.path.exists(COURSES_DIR):
        print(f"❌ Папка {COURSES_DIR} не найдена!")
        return []
    return [d for d in os.listdir(COURSES_DIR) if os.path.isdir(os.path.join(COURSES_DIR, d))]

def choose_course():
    """Выбор курса"""
    courses = list_courses()
    if not courses:
        print("Нет доступных курсов.")
        return None
    print("\n📚 Доступные курсы:")
    for i, course in enumerate(courses, 1):
        print(f"{i}) {course}")
    while True:
        choice = input("Выберите курс: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(courses):
            return courses[int(choice) - 1]
        print("⚠️ Неверный ввод, попробуйте снова.")

def load_questions(course):
    """Загрузка вопросов из выбранного курса"""
    file_path = os.path.join(COURSES_DIR, course, "questions.json")
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_result(course, score, total, exam_mode, passed=None):
    """Сохраняем результат в файл"""
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = "Экзамен" if exam_mode else "Тренировка"
        percent = (score / total * 100) if total > 0 else 0
        status = f" | СДАН ✅" if passed else (f" | НЕ СДАН ❌" if exam_mode else "")
        f.write(f"{timestamp} | {course} | {mode} | {score}/{total} ({percent:.1f}%) {status}\n")

def format_time(seconds_left):
    """Форматирование секунд в ЧЧ:ММ:СС"""
    h = seconds_left // 3600
    m = (seconds_left % 3600) // 60
    s = seconds_left % 60
    return f"{h:02}:{m:02}:{s:02}"

def progress_bar(current, total, length=30):
    """Рисует прогресс-бар"""
    percent = current / total
    filled = int(length * percent)
    bar = "█" * filled + "-" * (length - filled)
    return f"[{bar}] {current}/{total}"

def timer_thread(start_time):
    """Фоновый поток для обновления строки времени"""
    global stop_timer, time_string
    while not stop_timer:
        elapsed = int(time.time() - start_time)
        remaining = max(0, EXAM_TIME - elapsed)
        time_string = f"⏳ Осталось времени: {format_time(remaining)}"
        if remaining <= 0:
            break
        time.sleep(1)

def clear_screen():
    """Очищает консоль"""
    os.system("cls" if os.name == "nt" else "clear")

def ask_question(q, current, total):
    """Задает вопрос пользователю"""
    clear_screen()
    print(time_string)
    print(f"\nВопрос {current}/{total}:")
    print(q['question'])
    for idx, option in enumerate(q['options']):
        print(f"   {idx}) {option}")

    answer = input("\nВаш ответ (через запятую, если несколько): ").strip()
    try:
        user_choices = [int(x.strip()) for x in answer.split(",") if x.strip()]
    except ValueError:
        print("⚠️ Некорректный ввод, ответ засчитан как неверный.")
        return False

    if set(user_choices) == set(q['correct']):
        print("✅ Верно!")
        return True
    else:
        correct_answers = [q['options'][idx] for idx in q['correct']]
        print(f"❌ Неверно. Правильный ответ: {', '.join(correct_answers)}")
        return False

def training_mode(course, questions):
    """Режим тренировки"""
    queue = questions.copy()
    random.shuffle(queue)
    score = 0
    total = len(queue)
    answered = 0

    while queue:
        q = queue.pop(0)
        if ask_question(q, answered + 1, total):
            score += 1
        else:
            queue.append(q)
        answered += 1
        print("\n" + progress_bar(answered, total))
        input("Нажмите Enter для продолжения...")

    print("\n==== Итог (Тренировка) ====")
    print(f"Правильных: {score} из {total}")
    save_result(course, score, total, exam_mode=False)

def exam_mode(course, questions):
    """Режим экзамена"""
    global stop_timer, time_string
    selected = random.sample(questions, min(EXAM_QUESTIONS, len(questions)))
    score = 0
    total = len(selected)

    start_time = time.time()
    stop_timer = False
    timer = threading.Thread(target=timer_thread, args=(start_time,), daemon=True)
    timer.start()

    for i, q in enumerate(selected, 1):
        elapsed = int(time.time() - start_time)
        if elapsed > EXAM_TIME:
            clear_screen()
            print("\n⏰ Время вышло!")
            break

        if ask_question(q, i, total):
            score += 1

        print("\n" + progress_bar(i, total))
        input("Нажмите Enter для продолжения...")

    stop_timer = True
    timer.join()

    print("\n==== Итог (Экзамен) ====")
    print(f"Правильных: {score} из {total}")
    percent = score / total * 100
    print(f"Успеваемость: {percent:.1f}%")

    passed = score >= EXAM_PASS_SCORE
    if passed:
        print("🎉 Экзамен СДАН!")
    else:
        print("❌ Экзамен НЕ СДАН!")

    save_result(course, score, total, exam_mode=True, passed=passed)

if __name__ == "__main__":
    check_updates()
    course = choose_course()
    if not course:
        exit()

    questions = load_questions(course)
    if not questions:
        exit()

    print(f"\n📘 Тренажёр для подготовки: {course}")
    mode = input("Выберите режим (1 - тренировка, 2 - экзамен): ").strip()

    if mode == "2":
        exam_mode(course, questions)
    else:
        training_mode(course, questions)
