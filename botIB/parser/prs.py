import requests
import json
from pprint import pprint

class HeadHunter:
    __api_url = "https://api.hh.ru/vacancies"

    def __init__(self, keyword: str, page_count: int = 1, is_ignore: bool = True):
        self.keyword = keyword
        self.page_count = page_count
        self.is_ignore = is_ignore
        self.all_vacancies = self.get_all_vacancies()
        self.vacancies_data = []  # Список для хранения данных о вакансиях

    def get_all_vacancies(self):
        all_vacancies = []
        for page in range(self.page_count):
            print(f"Страница №{page + 1}:", end=' ')
            current_vacancies = self.get_vacancies_page(self.keyword, page)
            all_vacancies.extend(current_vacancies)
            
            if not current_vacancies:  # Если вакансий на странице нет, выходим из цикла
                print('Вакансий не найдено, завершение!')
                break

            print('OK!')

        print('-- ПОЛУЧИЛИ ВСЕ ВАКАНСИИ --')
        return all_vacancies

    def get_vacancies_page(self, keyword, page) -> list:
        request_params = {
            "text": keyword,
            "per_page": 100,
            "page": page,
            "area": 1  # ID для Москвы
        }

        headers = {
            "User-Agent": "Your User Agent"
        }

        response = requests.get(HeadHunter.__api_url, params=request_params, headers=headers)
        vacancies = []

        if response.status_code == 200:
            data = response.json()
            vacancies = data.get("items", [])
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

        return vacancies

    def get_vacancy_details(self, vacancy):
        vacancy_id = vacancy['id']
        title = vacancy['name']
        salary = self.get_vacancy_salary(vacancy)
        skills = self.get_vacancy_skills(vacancy_id)
        url = vacancy.get('alternate_url')  # Ссылка на вакансию
        self.vacancies_data.append({
            'id': vacancy_id,
            'title': title,
            'salary': salary,
            'key_skills': skills,
            'url': url  # Добавляем поле с ссылкой на вакансию
        })

    def get_vacancy_salary(self, vacancy) -> dict:
        salary = vacancy.get('salary')
        if salary and salary.get('from') is not None:
            salary_from = salary['from']
            salary_to = salary['to'] if salary.get('to') is not None else 'Не указано'
            currency = salary['currency']
            if currency == 'RUR':  # Ensure salary is in RUB
                return {'from': salary_from, 'to': salary_to, 'currency': currency}
        return {'from': None, 'to': None, 'currency': 'Не указано'}

    def get_vacancy_skills(self, vacancy_id) -> list:
        url = f"{self.__api_url}/{vacancy_id}"
        headers = {"User-Agent": "Your User Agent"}
        response_json = requests.get(url, headers=headers).text
        key_skills = json.loads(response_json).get('key_skills')

        if key_skills is not None:
            return [key_skill['name'] for key_skill in key_skills]
        return []

    def gather_vacancy_data(self):
        print('-- СОБИРАЕМ ДАННЫЕ ПО ВАКАНСИЯМ --')
        for vacancy in self.all_vacancies:
            print(f'Вакансия (id={vacancy["id"]}):', end=' ')
            self.get_vacancy_details(vacancy)
            print('OK!')

    def save_vacancies_to_file(self, filename='vacancies.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.vacancies_data, f, ensure_ascii=False, indent=4)
        print(f'-- ДАННЫЕ СОХРАНЕНЫ В ФАЙЛ {filename} --')

    def test(self):
        url = "https://api.hh.ru/vacancies/102832646"
        headers = {"User-Agent": "Your User Agent"}
        response_json = requests.get(url, headers=headers).text
        key_skills = json.loads(response_json).get('key_skills')
        if key_skills is not None:
            pprint([key_skill['name'] for key_skill in key_skills])
        else:
            print('Ошибка: key_skills is None, навыков нет!')


# for tests
if __name__ == '__main__':
    hh = HeadHunter(keyword='Информационная безопасность', page_count=3)  # Изменено на "Информационная безопасность"
    hh.gather_vacancy_data()
    hh.save_vacancies_to_file()
    hh.test()