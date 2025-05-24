import deepl
import os
from dotenv import load_dotenv


load_dotenv()

# DeepL 인증키
AUTH_KEY =  os.getenv("DEEPL_TOKEN") # 실제 발급받은 키로 교체

# DeepL 번역기 클라이언트 초기화
translator = deepl.Translator(AUTH_KEY)


def translate_sentences(sentences, target_lang="KO"):
  rows = len(sentences)
  cols = 2
  translated_sentences = [[0 for _ in range(cols)] for _ in range(rows)]

  for i, sentence in enumerate(sentences):
    if not sentence.strip():
      continue
    try:
      result = translator.translate_text(sentence, target_lang=target_lang)
      translated_sentences[i][0] = sentence
      translated_sentences[i][1] = result.text
    except Exception as e:
      translated_sentences.append(f"[Error translating] {sentence}")
      print("Error:", e)

  return translated_sentences
