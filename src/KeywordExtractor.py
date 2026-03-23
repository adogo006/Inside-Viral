from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
import json, math, os, re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_PATH, 'db_content.txt')
CACHE_PATH = os.path.join(BASE_PATH, 'sentiment_cache.json')
WEIGHTS_PATH = os.path.join(BASE_PATH, 'weights.json')

def load_data(path):
    if not os.path.exists(path):
        print(f"Error: {path} 파일이 없습니다.")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [repeat_normalize(line, num_repeats=2) for line in f.read().splitlines() if line.strip()]

def get_sentence_scores(sentences, classifier):
    # 1. 기존 문장 캐시 로드
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                if os.path.getsize(CACHE_PATH) > 0:
                    cache = json.load(f)
        except json.JSONDecodeError:
            print(f"[!] {CACHE_PATH}가 비어있거나 올바르지 않아 초기화합니다.")

    scores = []
    to_analyze = []
    analyze_indices = []

    # 2. 분석 필요한 문장 선별
    for i, s in enumerate(sentences):
        if s in cache:
            scores.append(cache[s])
        else:
            scores.append(None)
            to_analyze.append(s)
            analyze_indices.append(i)

    # 3. 새로운 문장 배치 분석
    if to_analyze:
        print(f"{len(to_analyze)}개 문장 분석 시작")
        CHUNK_SIZE = 32
        for i in range(0, len(to_analyze), CHUNK_SIZE):
            chunk = to_analyze[i : i + CHUNK_SIZE]
            chunk_indices = analyze_indices[i : i + CHUNK_SIZE]
        
            # 32청크 단위로 분석
            chunk_results = classifier(chunk, truncation=True, max_length=512, batch_size=CHUNK_SIZE)
            for sub_idx, res in enumerate(chunk_results):
                idx = chunk_indices[sub_idx]
                val = res['score'] if res['label'] == '1' else -res['score']
                scores[idx] = val
                cache[sentences[idx]] = val

                print(f"[{i + sub_idx + 1}/{len(to_analyze)}] {sentences[idx][:30]}... -> {val:.4f}")

            # 묶음 캐시 저장
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
            
    return scores

def calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid, classifier):
    word_extractor = WordExtractor()
    word_extractor.train(sentences)
    words = word_extractor.extract()

    filtered_candidates = {
        word: score for word, score in words.items()
        if re.search(r'[가-힣]', word) and
        score.leftside_frequency >= 5 and
        score.cohesion_forward >= 0.4 and
        score.right_branching_entropy >= 0.5
    }
    
    print(f"\n{len(filtered_candidates)}개 단어 모델 검증 시작")
    
    keyword_weights = {}
    for word, score in filtered_candidates.items():
        # 단어에 모델이 낸 점수가 극단적(0.95 이상)이면 알고있는 단어
        test_res = classifier(word, truncation=True)[0]
        model_confidence = test_res['score']
        # 모델 확신도가 너무 높으면 배제
        if model_confidence > 0.92:
            continue

        # 해당 단어가 포함된 문장 인덱스 추출
        indices = [i for i, s in enumerate(sentences) if word in s]
        if not indices: continue

        # 감성 증폭 (지수함수)
        avg_sent = sum(sentence_scores[i] for i in indices) / len(indices)
        sentiment_factor = math.exp(abs(avg_sent) * 3.0) * (1 if avg_sent > 0 else -1)

        # 의미론적 중요도
        word_centroid = torch.mean(all_embeddings[indices], dim=0)
        semantic_sim = util.cos_sim(word_centroid, dataset_centroid).item()

        # 신조어(model_confidence가 낮을수록) 가중치를 높여줌
        novelty_bonus = 2.0 - model_confidence

        # 최종 가중치 공식
        weight = (sentiment_factor * score.cohesion_forward) * (semantic_sim * novelty_bonus)
        
        # 가중치 임계값 필터링
        if abs(weight) > 0.5:
            keyword_weights[word] = round(weight, 4)

    return keyword_weights

def main():
    # 데이터 및 모델 로드
    sentences = load_data(FILE_PATH)
    if not sentences: return
    print("데이터 로드 완료")
    
    classifier = pipeline("sentiment-analysis", model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis")
    st_model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    print("모델 로드 완료")

    # 전체 문장 임베딩 및 중심점 계산
    # 의미가 비슷한 문장을 좌표 평면상에서 가까운 거리에 위치
    all_embeddings = st_model.encode(sentences, convert_to_tensor=True)
    # 문장들의 평균 위치인 중심점으로 데이터의 평균 주제를 도출
    dataset_centroid = torch.mean(all_embeddings, dim=0)
    print("문장 임베딩 및 중심점 계산 완료")

    # 감성 분석 (캐싱 포함)
    sentence_scores = get_sentence_scores(sentences, classifier)
    print("문장 캐싱 및 감정분석 완료")

    # 가중치 계산 및 저장
    weights = calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid, classifier)
    print("단어 가중치 계산 및 저장 완료")
    
    sorted_weights = dict(sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True))
    with open(WEIGHTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(sorted_weights, f, ensure_ascii=False, indent=4)
        
    print(f"\n-- 생성 완료: {WEIGHTS_PATH} --")

if __name__ == "__main__":
    main()