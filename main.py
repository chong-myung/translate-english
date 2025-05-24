from article_translate import translate_sentences
from article_crawling import get_koreaherald_article
from arrange_word import extract_vocab_and_phrases
from typing import List
from notion_client import Client

import os
from dotenv import load_dotenv

load_dotenv()

# Notion 설정
NOTION_KEY =  os.getenv("NOTION_TOKEN") # 실제 발급받은 키로 교체
notion = Client(auth=NOTION_KEY)
DATABASE_ID = "1f42dc82759b8010aff6e97ee2062b13"

class Word:

  def __init__(self, expression, meaning):
    self.expression = expression
    self.meaning = meaning

  def __eq__(self, other):
    return isinstance(other, Word) and self.expression == other.expression

  def __hash__(self):
    return hash(self.expression)

  def __repr__(self):
    return f"Word(expression='{self.expression}', meaning='{self.meaning}')"

class ArticleData:

  def __init__(self, page_id : str, title: str, content: List[List[str]], words: List[Word], phrases: List[Word]):
    self.page_id = page_id
    self.title = title
    self.content = content
    self.words = words
    self.phrases = phrases


chunk_size = 3

def get_url_list():
  results = []
  response = notion.databases.query(
    database_id=DATABASE_ID,
    filter={
      "and": [
        {
          "property": "URL",
          "url": {
            "is_not_empty": True
          }
        },
        {
          "property": "번역상태",
          "status": {
            "equals": "번역 전"
          }
        }
      ]
    }
  )

  for page in response['results']:
    props = page['properties']
    if 'URL' in props:
      url = props['URL']['url']
      results.append((page['id'], url))
  return results

def create_article():
  url_map = get_url_list()

  for page_id,url in url_map:
    try:
      article = translate_article(page_id, url)
      update_article_page(article)
      update_status(page_id, True, article.title)
      print(f"✅ Success register Article : {page_id}")
    except Exception as e:
      print(e)
      update_status(page_id,False,"")
      print(f"😡 Fail register Article : {page_id}")

  return 0


def translate_article(page_id,url):
  article = get_koreaherald_article(url)
  title = article['title']
  content_list = article['content'].split('\n')
  content_result = []

  for content in content_list:
    if not content.strip():
      continue
    content_result.append(content.strip())

  content_translate = translate_sentences(content_result)

  unique_words = []
  unique_phrases = []
  for i in range(0, len(content_translate), chunk_size):
    chunk = content_translate[i:i + chunk_size]
    lines = [row[0] for row in chunk]
    joined = '\n'.join(lines)
    data = extract_vocab_and_phrases(joined)
    words = [Word(item['expression'], item['meaning']) for item in data.get("words", [])]
    phrases = [Word(item['expression'], item['meaning']) for item in data.get("phrases", [])]

    unique_words.extend(words)
    unique_phrases.extend(phrases)

  return ArticleData(page_id,title, content_translate, unique_words ,unique_phrases)


def update_article_page(article: ArticleData):
  page_id = article.page_id.replace("-","")

  # 1. 기존 블록 가져오기
  blocks = notion.blocks.children.list(page_id)["results"]

  # 2. 기존 블록 삭제 (Notion API는 직접 삭제 지원 X → 대신 '아카이브')
  for block in blocks:
    block_id = block["id"]
    notion.blocks.update(block_id, archived=True)

  # 3. 새로운 블록 생성
  new_blocks = article_to_notion_blocks(article)

  # 4. 페이지에 새 블록 children 추가

  for chunk in chunked_blocks(new_blocks, 100):
    notion.blocks.children.append(
      block_id=page_id,
      children=chunk
    )

def article_to_notion_blocks(article: ArticleData) -> List[dict]:
  def text_block(text: str, heading: int = None):
    if heading == 1:
      return {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
          "rich_text": [{"type": "text", "text": {"content": text}}]
        }
      }
    elif heading == 2:
      return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
          "rich_text": [{"type": "text", "text": {"content": text}}]
        }
      }
    elif heading == 3:
      return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
          "rich_text": [{"type": "text", "text": {"content": text}}]
        }
      }
    else:
      return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": text}}]
        }
      }

  def bullet_block(word: Word):
    return {
      "object": "block",
      "type": "bulleted_list_item",
      "bulleted_list_item": {
        "rich_text": [{
          "type": "text",
          "text": {
            "content": f"{word.expression} ⟶ `{word.meaning}`"
          }
        }]
      }
    }

  # content_text = "\n\n".join([" ".join(sentence) for sentence in article.content])
  content_text = [text_block(sentence[0]+"\n"+sentence[1]) for sentence in article.content]
  phrases = [bullet_block(p) for p in article.phrases]
  words = [bullet_block(w) for w in article.words]

  blocks = [
    text_block("본문", heading=2),
    *(content_text or []),
    text_block("🔥중요 숙어", heading=3),
    *(phrases or [bullet_block(Word("없음", "없음"))]),
    text_block("📖중요 단어", heading=3),
    *(words or [bullet_block(Word("없음", "없음"))])
  ]

  return blocks


def chunked_blocks(blocks, chunk_size=100):
  for i in range(0, len(blocks), chunk_size):
    yield blocks[i:i + chunk_size]

def update_status(page_id:str,success_flag:bool,title:str =""):
  status = ""
  if success_flag:
    status = "번역완료"
  else:
    status = "번역실패"
  notion.pages.update(
    page_id=page_id,
    properties={
      "제목": {
        "title": [
          {
            "type": "text",
            "text": {"content": title}
          }
        ]
      },
      "번역상태": {
        "status": {"name": status}
      }
    }
  )


create_article()






