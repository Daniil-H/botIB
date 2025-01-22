import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from collections import Counter
import statistics
import matplotlib.pyplot as plt  
import os

# Загрузка данных из JSON файла
with open('vacancies.json', 'r', encoding='utf-8') as f:
    vacancies_data = json.load(f)

# Убираем выделенный текст из требований и возвращаем уникальные навыки
def clean_skills(skills):
    cleaned = set()
    if not isinstance(skills, list):
        return cleaned

    for skill in skills:
        if isinstance(skill, str):
            cleaned.add(skill.strip())
    return list(cleaned)

# Функция для извлечения и парсинга зарплаты
def parse_salary(salary_info):
    salaries = []
    if salary_info is None:
        return salaries
    
    if 'from' in salary_info and salary_info['from'] is not None:
        salaries.append(salary_info['from'])
    if 'to' in salary_info and salary_info['to'] is not None:
        salaries.append(salary_info['to'])
    
    return [sal for sal in salaries if isinstance(sal, (int, float))]

# Получение информации по конкретной вакансии
def get_vacancy_info(vacancy_name, data):
    matched_vacancies = [item for item in data if vacancy_name.lower() in item['title'].lower()]

    if not matched_vacancies:
        return None

    count = len(matched_vacancies)
    salaries = []
    skills = []
    links = []
    
    for item in matched_vacancies:
        salary_info = item['salary']
        salaries.extend(parse_salary(salary_info))
        skills.extend(item.get('key_skills', []))
        links.append(item['url'])

    return {
        'count': count,
        'salary_analysis': salaries,
        'skills': clean_skills(skills),
        'links': links
    }

def create_salary_plot(vacancy_salaries_dict, y_tick_fontsize=8):
    plt.figure(figsize=(12, 6))
    
    all_vacancies = list(vacancy_salaries_dict.keys())
    all_salaries = [statistics.mean(salaries) for salaries in vacancy_salaries_dict.values()]

    # Сортируем данные для лучшего отображения
    sorted_indices = sorted(range(len(all_salaries)), key=lambda k: all_salaries[k])
    sorted_salaries = [all_salaries[i] for i in sorted_indices]
    sorted_vacancies = [all_vacancies[i] for i in sorted_indices]
    
    plt.barh(sorted_vacancies, sorted_salaries, color='skyblue')
    plt.xlabel('Средняя зарплата (рублей)', fontsize=12)
    plt.ylabel('Вакансии', fontsize=12)
    plt.title('Средняя зарплата по вакансиям', fontsize=14)
    plt.grid(axis='x')
    
    plt.yticks(fontsize=y_tick_fontsize)  # Уменьшаем размер шрифта для оси Y
    
    plot_path = 'salary_plot.png'
    plt.savefig(plot_path)
    plt.close()
    return plot_path

def create_skills_plot(skills_count_dict, y_tick_fontsize=8):
    plt.figure(figsize=(12, 6))

    all_skills = list(skills_count_dict.keys())
    all_counts = list(skills_count_dict.values())

    # Сортируем данные для лучшего отображения
    sorted_indices = sorted(range(len(all_counts)), key=lambda k: all_counts[k], reverse=True)
    sorted_counts = [all_counts[i] for i in sorted_indices]
    sorted_skills = [all_skills[i] for i in sorted_indices]

    plt.barh(sorted_skills[:10], sorted_counts[:10], color='lightcoral')  # Сохраняем только топ-10 навыков
    plt.xlabel('Количество вакансий', fontsize=12)
    plt.ylabel('Навыки', fontsize=12)
    plt.title('Топ навыков по количеству вакансий', fontsize=14)
    plt.grid(axis='x')

    plt.yticks(fontsize=y_tick_fontsize)  # Уменьшаем размер шрифта для оси Y

    plot_path = 'skills_plot.png'
    plt.savefig(plot_path)
    plt.close()
    return plot_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Привет! Я ваш помощник по поиску вакансий. 🤖\n"
        "Вы можете использовать следующие команды:\n"
        "/vacancy <название вакансии> - получить информацию о вакансиях по указанному названию.\n"
        "/links <название вакансии> - получит только ссылки на вакансии по указанному названию.\n"
        "/analytics <название вакансии> - получит только аналитику по вакансиям (зарплата и навыки).\n"
        "/salary_plot <название вакансии> - получить график распределения зарплат.\n"
        "/top_salary_vacancies - получить топ 10 вакансий по среднему уровню зарплаты.\n"
        "/top_skills - получить график топ навыков по количеству вакансий.\n"
        "Например: /vacancy Python Developer"
    )
    if update.message:
        await update.message.reply_text(welcome_message)

async def handle_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        vacancy_name = ' '.join(context.args)
        vacancy_info = get_vacancy_info(vacancy_name, vacancies_data)

        response_message = ""
        if vacancy_info:
            response_message += f"🔍 Количество вакансий по '{vacancy_name}': {vacancy_info['count']}\n"
            if vacancy_info['salary_analysis']:
                avg_salary = round(statistics.mean(vacancy_info['salary_analysis']))
                response_message += f"💰 Средний уровень зарплаты: {avg_salary} рублей\n"
            else:
                response_message += "🚫 Зарплата не указана.\n"

            if vacancy_info['skills']:
                unique_skills = set(vacancy_info['skills'])
                response_message += "✔️ Навыки кандидатов:\n" + "\n".join(unique_skills) + "\n"
            else:
                response_message += "🚫 Навыки не указаны.\n"

            response_message += "🔗 Ссылки на вакансии:\n" + "\n".join(vacancy_info['links']) + "\n"
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(f"❌ Вакансии по '{vacancy_name}' не найдены.")
    else:
        await update.message.reply_text("🚫 Пожалуйста, укажите название вакансии.")

async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        vacancy_name = ' '.join(context.args)
        vacancy_info = get_vacancy_info(vacancy_name, vacancies_data)

        response_message = ""
        if vacancy_info:
            if vacancy_info['links']:
                response_message = "🔗 Ссылки на вакансии:\n" + "\n".join(vacancy_info['links']) + "\n"
            else:
                response_message = "🚫 Ссылки на вакансии не найдены."
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(f"❌ Вакансии по '{vacancy_name}' не найдены.")
    else:
        await update.message.reply_text("🚫 Пожалуйста, укажите название вакансии.")

async def handle_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        vacancy_name = ' '.join(context.args)
        vacancy_info = get_vacancy_info(vacancy_name, vacancies_data)

        response_message = ""
        if vacancy_info:
            response_message += f"🔍 Аналитика по вакансиям '{vacancy_name}':\n"
            if vacancy_info['salary_analysis']:
                avg_salary = round(statistics.mean(vacancy_info['salary_analysis'])) 
                response_message += f"💰 Средний уровень зарплаты: {avg_salary} рублей\n"
            else:
                response_message += "🚫 Зарплата не указана.\n"

            if vacancy_info['skills']:
                unique_skills = set(vacancy_info['skills'])
                response_message += "✔️ Навыки кандидатов:\n" + "\n".join(unique_skills) + "\n"
            else:
                response_message += "🚫 Навыки не указаны.\n"

            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(f"❌ Вакансии по '{vacancy_name}' не найдены.")
    else:
        await update.message.reply_text("🚫 Пожалуйста, укажите название вакансии.")

async def handle_salary_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        vacancy_name = ' '.join(context.args)
        vacancy_info = get_vacancy_info(vacancy_name, vacancies_data)

        response_message = ""
        if vacancy_info:
            if vacancy_info['salary_analysis']:
                plot_path = create_salary_plot({vacancy_name: vacancy_info['salary_analysis']})
                response_message += f"🌍 Распределение зарплат по вакансии '{vacancy_name}':\n"
                await update.message.reply_text(response_message)
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(plot_path, 'rb'))
                os.remove(plot_path)
            else:
                await update.message.reply_text("🚫 Зарплата не указана для данной вакансии.")
        else:
            await update.message.reply_text(f"❌ Вакансии по '{vacancy_name}' не найдены.")
    else:
        await update.message.reply_text("🚫 Пожалуйста, укажите название вакансии.")

async def handle_top_salary_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vacancy_salaries_dict = {}
    for item in vacancies_data:
        title = item['title']
        # Фильтруем вакансии, чтобы не включать вакансии архитектора
        if 'архитектор' in title.lower():
            continue
        salaries = parse_salary(item.get('salary'))
        if salaries:
            vacancy_salaries_dict[title] = salaries

    # Сортируем вакансии по средней зарплате
    top_vacancies = sorted(vacancy_salaries_dict.items(), key=lambda x: statistics.mean(x[1]), reverse=True)[:10]

    if top_vacancies:
        response_message = "🏆 Топ 10 вакансий по средней зарплате:\n"
        for title, salaries in top_vacancies:
            avg_salary = round(statistics.mean(salaries))
            response_message += f"{title}: {avg_salary} рублей\n"
        
        # Создаем график для топ-10 вакансий
        top_salary_dict = {title: salaries for title, salaries in top_vacancies}
        plot_path = create_salary_plot(top_salary_dict, y_tick_fontsize=7)  # Уменьшаем размер шрифта для графика 

        await update.message.reply_text(response_message)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(plot_path, 'rb'))
        os.remove(plot_path)  # Удаляем файл графика после отправки
    else:
        await update.message.reply_text("🚫 Нет доступных вакансий для отображения.")

async def handle_top_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skills_count_dict = Counter()

    for item in vacancies_data:
        skills = clean_skills(item.get('key_skills', []))
        skills_count_dict.update(skills)  # Подсчитываем количество вакансий для каждого навыка

    plot_path = create_skills_plot(skills_count_dict, y_tick_fontsize=7)  # Уменьшаем размер шрифта для графика
    
    response_message = "📊 Топ навыков по количеству вакансий:\n"
    await update.message.reply_text(response_message)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(plot_path, 'rb'))
    os.remove(plot_path)

# Настройка бота
def main():
    app = ApplicationBuilder().token('ТОКЕН').build()  

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vacancy", handle_vacancy))
    app.add_handler(CommandHandler("links", handle_links))
    app.add_handler(CommandHandler("analytics", handle_analytics))
    app.add_handler(CommandHandler("salary_plot", handle_salary_plot))
    app.add_handler(CommandHandler("top_salary_vacancies", handle_top_salary_vacancies))  # Новый обработчик
    app.add_handler(CommandHandler("top_skills", handle_top_skills))

    app.run_polling()

if __name__ == "__main__":
    main()
