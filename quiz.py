import json
import random
import os
import time
import threading
import sys
from datetime import datetime

# Файлы
QUESTIONS_FILE = "questions_full.json"
RESULTS_FILE = "results.txt"

# Настройки экзамена
EXAM_TIME = 3600          # 1 час = 3600 секунд
EXAM_QUESTIONS = 45       # количество вопросов в экзамене
EXAM_PASS_SCORE = 38      # порог сдачи

stop_timer = False  # глобальный флаг для остановки таймера
time_string = ""    # глобальная строка для текущего времени

def load_questions(filename=QUESTIONS_FILE):
    """Загрузка вопросов из JSON"""
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден!")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_result(score, total, exam_mode, passed=None):
    """Сохраняем результат в файл"""
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = "Экзамен" if exam_mode else "Тренировка"
        percent = (score / total * 100) if total > 0 else 0
        status = f" | СДАН ✅" if passed else (f" | НЕ СДАН ❌" if exam_mode else "")
        f.write(f"{timestamp} | {mode} | {score}/{total} ({percent:.1f}%) {status}\n")

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
    """Очищает консоль (кроссплатформенно)"""
    os.system("cls" if os.name == "nt" else "clear")

def ask_question(q, current, total):
    """Задает вопрос пользователю и возвращает True/False"""
    clear_screen()
    print(time_string)  # время сверху
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

def training_mode(questions):
    """Режим тренировки без времени. Ошибочные вопросы повторяются."""
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
            queue.append(q)  # возвращаем вопрос в конец очереди
        answered += 1
        print("\n" + progress_bar(answered, total))
        input("Нажмите Enter для продолжения...")

    print("\n==== Итог (Тренировка) ====")
    print(f"Правильных: {score} из {total}")
    print("🎯 Все вопросы были пройдены!")
    save_result(score, total, exam_mode=False)

def exam_mode(questions):
    """Режим экзамена — 45 вопросов, 1 час"""
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

    save_result(score, total, exam_mode=True, passed=passed)

if __name__ == "__main__":
    questions = load_questions()
    if not questions:
        exit()

    print("📘 Тренажёр для подготовки к экзамену PT-SIEM-CS")
    mode = input("Выберите режим (1 - тренировка, 2 - экзамен): ").strip()

    if mode == "2":
        exam_mode(questions)
    else:
        training_mode(questions)
