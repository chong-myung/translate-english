import requests
from bs4 import BeautifulSoup

def get_koreaherald_article(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # 제목 추출
    section_tag = soup.find('section', class_='view_top')  # 제목
    if section_tag is None:
        section_tag = soup.find('section', class_='series_view_top')  # 제목

    title_tag = section_tag.find('div',class_='news_title')
    if title_tag is None:
        title_tag = section_tag.find("article")

    title = title_tag.find('h1').get_text(strip=True) if title_tag else 'No title found'

    # 본문 추출
    body_div = soup.find('article', class_='news_content')

    if body_div:
        paragraphs = body_div.find_all('p')
        content = '\n'.join(p.get_text(strip=True) for p in paragraphs)
    else:
        content = 'No content found'

    return {
        'title': title,
        'content': content
    }
