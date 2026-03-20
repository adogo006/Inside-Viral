from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
import json, math, os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_PATH, 'db_content.txt')
CACHE_PATH = os.path.join(BASE_PATH, 'sentiment_cache.json')
WEIGHTS_PATH = os.path.join(BASE_PATH, 'weights.json')

# 단음절 조사 배제 리스트
PARTICLES = set(["은", "는", "이", "가", "을", "를", "의", "야", "아", "들", "에", "로", "와", "과", "랑", "도", "만", "나", "요", "서", "?", "!", ".", ","])

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
                else:
                    cache = {}
        except json.JSONDecodeError:
            print(f"[!] {CACHE_PATH}가 비어있거나 올바르지 않아 초기화합니다.")
            cache = {}

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
                original_idx = chunk_indices[sub_idx]
                val = res['score'] if res['label'] == '1' else -res['score']
            
                scores[original_idx] = val
                cache[sentences[original_idx]] = val

                print(f"[{i + sub_idx + 1}/{len(to_analyze)}] {sentences[original_idx][:30]}... -> {val:.4f}")

            # 묶음 캐시 저장
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
            
    return scores

def calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid):
    word_extractor = WordExtractor()
    word_extractor.train(sentences)
    words = word_extractor.extract()

    # 1. 단어 필터링 (엔트로피, 응집도 기준)
    filtered = {
        word: score for word, score in words.items()
        if word not in PARTICLES and
        score.leftside_frequency >= 5 and
        score.cohesion_forward >= 0.4 and
        score.right_branching_entropy >= 0.8
    }
    
    print(f"\n선별된 단어: {len(filtered)}개")
    
    keyword_weights = {}
    for word, score in filtered.items():
        # 해당 단어가 포함된 문장 인덱스 추출
        indices = [i for i, s in enumerate(sentences) if word in s]
        if not indices: continue

        # 감성 증폭 (지수함수 활용)
        avg_sent = sum(sentence_scores[i] for i in indices) / len(indices)
        sentiment_factor = math.exp(abs(avg_sent) * 3.0) * (1 if avg_sent > 0 else -1)

        # 의미론적 중요도 (SBERT)
        word_centroid = torch.mean(all_embeddings[indices], dim=0)
        semantic_sim = util.cos_sim(word_centroid, dataset_centroid).item()

        # 최종 가중치 공식
        freq_bonus = math.log(score.leftside_frequency + 1)
        weight = (sentiment_factor * score.cohesion_forward) * (semantic_sim + 0.1 * freq_bonus)
        
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
    all_embeddings = st_model.encode(sentences, convert_to_tensor=True)
    dataset_centroid = torch.mean(all_embeddings, dim=0)
    print("문장 임베딩 및 중심점 계산 완료")

    # 감성 분석 (캐싱 포함)
    sentence_scores = get_sentence_scores(sentences, classifier)
    print("문장 캐싱 및 감정분석 완료")

    # 가중치 계산 및 저장
    weights = calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid)
    print("단어 가중치 계산 및 저장 완료")
    
    with open(WEIGHTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(weights, f, ensure_ascii=False, indent=4)
        
    print(f"\n-- 생성 완료: {WEIGHTS_PATH} --")

if __name__ == "__main__":
    main()