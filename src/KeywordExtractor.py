from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
import json, math, os, time

# 단음절 조사, 특수문자는 keyword 추출에서 배제하기 위함
particle = ["은", "는", "이", "가", "을", "를", "의", "야", "아", "들",
            "에", "로", "와", "과", "랑", "도", "만", "나", "요", "서",
            "?", "!", ".", ","]

# db_content.txt 내용 읽어오기
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'db_content.txt')
with open(file_path, 'r', encoding='utf-8') as f:
    sentences = [repeat_normalize(line, num_repeats=2) for line in f.read().splitlines()]

# 모델 로드
MODEL_WORDEXTRACTOR = "jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
MODEL_TRANSFORMER = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

classifier = pipeline("sentiment-analysis", model=MODEL_WORDEXTRACTOR)

st_model = SentenceTransformer(MODEL_TRANSFORMER)
all_embeddings = st_model.encode(sentences, convert_to_tensor=True)
dataset_centroid = torch.mean(all_embeddings, dim=0)

print("\n모델 로드 완료\n")
    
def build_keyword_weights(sentences):
    word_extractor = WordExtractor()
    word_extractor.train(sentences)
    words = word_extractor.extract()

    # word 예외처리
    filtered_words = []
    for word, score in words.items():
        if word in particle:
            continue
        if score.leftside_frequency < 5:
            continue
        if score.cohesion_forward < 0.4:
            continue
        if score.right_branching_entropy < 0.8:
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
        # *******
        # 거듭 제곱이 아닌 지수함수를 활용하여 평균 감정의 영향이 가중치에 더 크게 반영되도록 변경해야함
        # *******
        avg_sentiment = sum(sentence_score[i] for i in indice) / len(indice)
        sign = 1 if avg_sentiment > 0 else -1
        avg_sentiment = sign * (abs(avg_sentiment) ** 2)
        
        # 가중치 연산
        # 의미론적 중요도: 이 단어가 포함된 문장들이 전체 주제와 얼마나 일치하는가
        word_sentences_embedding = all_embeddings[indice]
        word_centroid = torch.mean(word_sentences_embedding, dim=0)
        semantic_importance = util.cos_sim(word_centroid, dataset_centroid).item()

        # 최종 공식: (감성 * 응집도) * log(중요도 + 빈도보정)
        freq_bonus = math.log(words[word].leftside_frequency + 1)
        weight = (avg_sentiment * words[word].cohesion_forward) * (semantic_importance + 0.1 * freq_bonus)
        
        keyword_weights[word] = round(weight, 4)
        
        # debug
        print(f"\n[{idx}/{max_cnt}]  \"{word}\"  weight: {keyword_weights[word]}\n")

    with open('weights.json', 'w', encoding='utf-8') as f:
        json.dump(keyword_weights, f, ensure_ascii=False, indent=4)
    print("\n--키워드의 가중치 모음(weights.json) 생성 완료--\n")
        
if __name__ == "__main__":
    build_keyword_weights(sentences)