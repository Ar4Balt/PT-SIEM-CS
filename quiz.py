import json
import random
import os
import time
from datetime import datetime

# Файлы
QUESTIONS_FILE = "questions_full.json"
RESULTS_FILE = "results.txt"

# Настройки экзамена
EXAM_TIME = 3600          # 1 час = 3600 секунд
EXAM_QUESTIONS = 45       # количество вопросов в экзамене
EXAM_PASS_SCORE = 38      # порог сдачи

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

def ask_question(q):
    """Задает вопрос пользователю и возвращает True/False"""
    print(f"\n{q['question']}")
    for idx, option in enumerate(q['options']):
        print(f"   {idx}) {option}")

    answer = input("Ваш ответ (через запятую, если несколько): ").strip()
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

    while queue:
        q = queue.pop(0)
        if ask_question(q):
            score += 1
        else:
            queue.append(q)  # возвращаем вопрос в конец очереди

    print("\n==== Итог (Тренировка) ====")
    print(f"Правильных: {score} из {total}")
    print("🎯 Все вопросы были пройдены!")
    save_result(score, total, exam_mode=False)

def exam_mode(questions):
    """Режим экзамена — 45 вопросов, 1 час"""
    selected = random.sample(questions, min(EXAM_QUESTIONS, len(questions)))
    score = 0
    total = len(selected)

    start_time = time.time()
    for i, q in enumerate(selected, 1):
        if (time.time() - start_time) > EXAM_TIME:
            print("\n⏰ Время вышло!")
            break

        print(f"\nВопрос {i}/{total}:")
        if ask_question(q):
            score += 1

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
