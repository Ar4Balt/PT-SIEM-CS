import json
import random
import os
import time

# Файл с полным набором вопросов
QUESTIONS_FILE = "questions_full.json"

def load_questions(filename=QUESTIONS_FILE):
    """Загрузка вопросов из JSON"""
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден!")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def run_quiz(questions, exam_mode=False, exam_time=600):
    """
    Запуск тренажёра
    exam_mode = True → включается режим экзамена
    exam_time → лимит времени в секундах
    """
    random.shuffle(questions)
    score = 0
    total = len(questions)

    start_time = time.time()

    for i, q in enumerate(questions, 1):
        if exam_mode and (time.time() - start_time) > exam_time:
            print("\n⏰ Время вышло!")
            break

        print(f"\n{i}. {q['question']}")
        for idx, option in enumerate(q['options']):
            print(f"   {idx}) {option}")

        answer = input("Ваш ответ (через запятую, если несколько): ").strip()
        try:
            user_choices = [int(x.strip()) for x in answer.split(",") if x.strip()]
        except ValueError:
            print("⚠️ Некорректный ввод, пропускаем вопрос.")
            continue

        if set(user_choices) == set(q['correct']):
            print("✅ Верно!")
            score += 1
        else:
            correct_answers = [q['options'][idx] for idx in q['correct']]
            print(f"❌ Неверно. Правильный ответ: {', '.join(correct_answers)}")

    print("\n==== Итог ====")
    print(f"Правильных: {score} из {total}")
    print(f"Успеваемость: {score/total*100:.1f}%")

if __name__ == "__main__":
    questions = load_questions()
    if not questions:
        exit()

    print("📘 Тренажёр для подготовки к экзамену PT-SIEM-CS")
    mode = input("Выберите режим (1 - тренировка, 2 - экзамен): ").strip()

    if mode == "2":
        run_quiz(questions, exam_mode=True, exam_time=600)  # экзамен 10 минут
    else:
        run_quiz(questions, exam_mode=False)
