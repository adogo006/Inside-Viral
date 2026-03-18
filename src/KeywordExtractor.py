from soynlp.word import WordExtractor
from transformers import pipeline
import json
import math
import os

# 단음절 조사, 특수문자는 keyword 추출에서 배제하기 위함
particle = ["은", "는", "이", "가", "을", "를", "의", "야", "아", "들",
            "에", "로", "와", "과", "랑", "도", "만", "나", "요", "서",
            "?", "!", ".", ","]

MODEL = "jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
classifier = pipeline("sentiment-analysis", model=MODEL)
print("\n--모델 로드 완료--\n")

def build_keyword_weights(sentences):
    word_extractor = WordExtractor()
    word_extractor.train(sentences)
    words = word_extractor.extract()

    keyword_weights = {}
    
    for word, score in words.items():
        if word in particle: continue   # 예외처리
        #if score.leftside_frequency < 1: continue   # 예외처리: 사용빈도가 적은 단어
        
        # word가 포함된 모든 문장
        relevant_sentences = [s for s in sentences if word in s]
        if not relevant_sentences: continue
        
        total_sentiment = 0
        for s in relevant_sentences:
            res = classifier(s)[0]
            print(f"{s} : {res}")
            score_val = res['score'] if res['label'] == 'LABEL_1' else -res['score']
            total_sentiment += score_val
        avg_sentiment = total_sentiment / len(relevant_sentences)
        
        # 가중치 = 평균 감정 * 중요도(log 빈도 * 응집도)
        importance = math.log(score.leftside_frequency + 1) * score.cohesion_forward
        weight = avg_sentiment * importance
        
        c = 0.5 if len(word) == 1 else 1.0 # 단음절 감쇄용 상수
        keyword_weights[word] = round(weight * c, 4)
        print(f"\n--{word} : weight = {keyword_weights[word]}--\n")

    with open('weights.json', 'w', encoding='utf-8') as f:
        json.dump(keyword_weights, f, ensure_ascii=False, indent=4)
    print("\n--키워드의 가중치 모음(weights.json) 생성 완료--\n")
        
if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'sentences.txt')

    with open(file_path, 'r', encoding='utf-8') as f:
        sentences = f.read().splitlines()
        
    build_keyword_weights(sentences)