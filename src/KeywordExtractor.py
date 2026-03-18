from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
import json
import math
import os
import time

# 단음절 조사, 특수문자는 keyword 추출에서 배제하기 위함
particle = ["은", "는", "이", "가", "을", "를", "의", "야", "아", "들",
            "에", "로", "와", "과", "랑", "도", "만", "나", "요", "서",
            "?", "!", ".", ","]

MODEL = "jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
classifier = pipeline("sentiment-analysis", model=MODEL)
print("\n모델 로드 완료\n")

def build_keyword_weights(sentences):
    word_extractor = WordExtractor()
    word_extractor.train(sentences)
    words = word_extractor.extract()

    # word 예외처리
    filtered_words = []
    for word, score in words.items():
        if word in particle or len(word) < 2:
            continue
        if score.leftside_frequency < 5:
            continue
        if score.cohesion_forward < 0.2:
            continue
        if score.right_branching_entropy < 0.5:
            continue
        filtered_words.append(word)
    
    print(f"\n전체 추출 단어 {len(words)}개 중 {len(filtered_words)}개 선별\n")
    time.sleep(2)
    
    print(f"\n{len(sentences)}개 문장 감성 분석\n")
    time.sleep(2)
    
    # 문장 sentiment 설정
    sentence_score = []
    for s in sentences:
        res = classifier(s, truncation=True, max_length=512)[0]
        val = res['score'] if res['label'] == '1' else -res['score']
        sentence_score.append(val)
        
        #debug
        print(f"[{sentences.index(s)}/{len(sentences)}]  \"{s}\"\n{res}")
    
    print(f"\n문장 감성 분석 완료 및 가중치 계산 시작\n")
    time.sleep(2)
    
    keyword_weights = {}
    max_cnt = len(filtered_words)
    
    for idx, word in enumerate(filtered_words):
        score = words[word]
        
        indice = [i for i, s in enumerate(sentences) if word in s]
        if not indice: continue
        
        avg_sentiment = sum(sentence_score[i] for i in indice) / len(indice)
        
        # 가중치 연산
        strength = abs(avg_sentiment) 
        weight = (strength * score.cohesion_forward) + (0.3 * math.log(score.leftside_frequency + 1))
        if avg_sentiment < 0:
            weight = -weight

        keyword_weights[word] = round(weight, 4)
        
        # debug
        print(f"\n[{idx}/{max_cnt}]  \"{word}\"  weight: {keyword_weights[word]}\n")

    with open('weights.json', 'w', encoding='utf-8') as f:
        json.dump(keyword_weights, f, ensure_ascii=False, indent=4)
    print("\n--키워드의 가중치 모음(weights.json) 생성 완료--\n")
        
if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'db_content.txt')

    with open(file_path, 'r', encoding='utf-8') as f:
        sentences = [repeat_normalize(line, num_repeats=2) for line in f.read().splitlines()]
        
    build_keyword_weights(sentences)