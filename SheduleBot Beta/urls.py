import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def fetch_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем наличие ошибок при запросе
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # Находим все элементы <a> с классом 'left_group'
        links = soup.find_all('a', class_='left_group')

        # Извлекаем ссылки из найденных элементов и добавляем префикс к каждой ссылке
        urls = [urljoin(url, link['href']) for link in links]

        return urls
    except requests.exceptions.RequestException as e:
        print(f"Error fetching links: {e}")
        return None

def fetch_links_from_each_page(links):
    all_links = []
    for link in links:
        try:
            print(f"Processing: {link}")
            response = requests.get(link)
            response.raise_for_status()  # Проверяем наличие ошибок при запросе
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Находим элемент <select>
            select_element = soup.find('select', onchange=True)

            # Если найден элемент <select>
            if select_element:
                # Находим все элементы <option> внутри элемента <select>
                options = select_element.find_all('option')

                # Извлекаем значения атрибута 'value' из элементов <option>,
                # исключая элемент с атрибутом 'selected'
                page_links = [urljoin(link, option['value']) for option in options if not option.get('selected')]
                
                all_links.extend(page_links)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching links from page {link}: {e}")

    return all_links

def main():
    url = "https://colportal.uni-college.ru/rasp/index.php"
    parsed_links = fetch_links(url)
    if parsed_links:
        extracted_links = fetch_links_from_each_page(parsed_links)
        if extracted_links:
            # Сохраняем список ссылок в файл JSON
            with open("extracted_links.json", "w") as f:
                json.dump(extracted_links, f)

if __name__ == "__main__":
    main()
