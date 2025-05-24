import os
from dotenv import load_dotenv
import openai
import json
import re


load_dotenv()

client = openai.OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

def extract_vocab_and_phrases(article_text):
  prompt = build_prompt(article_text)

  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are an English teacher at the high school level in South Korea."},
      {"role": "user", "content": prompt}
    ],
    temperature=0.4,
    max_tokens=1000,
  )

  raw_output = response.choices[0].message.content.strip()
  raw_output = clean_gpt_json(raw_output)
  # JSON 파싱 시도
  try:
    data = json.loads(raw_output)
  except json.JSONDecodeError:
    print("[⚠️ GPT 출력이 JSON 형식이 아닐 수 있습니다. 원본 출력 확인 필요]")
    data = {"words": [], "phrases": []}

  return data

def clean_gpt_json(raw_output: str):
    # 코드 블럭 제거
    cleaned = re.sub(r"^```json|```$", "", raw_output.strip(), flags=re.MULTILINE)
    return cleaned.strip()

def build_prompt(article_text):
  return f"""
Extract useful English words and idioms for Korean high school students. 
Output as JSON: 
{{
  "words": [{{"expression": "word", "meaning": "Korean meaning"}}],
  "phrases": [{{"expression": "phrase", "meaning": "Korean meaning"}}]
}}
Do not include explanations or markdown formatting.
Text:
\"\"\"
{article_text}
\"\"\"
""".strip()