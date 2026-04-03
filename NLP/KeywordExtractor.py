# docker exec -it insideviral_devcontainer-crawler-1 python3 main.py  :: 크롤링 컨테이너에서 크롤링 시작
# docker logs -f insideviral_devcontainer-crawler-1 :: 크롤링 컨테이너 로그 보기
# insideviral_devcontainer-crawler-1 :: 크롤러 컨테이너 이름

from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
import math, re

def get_sentence_scores(sentences, classifier):
    scores = []
    CHUNK_SIZE = 32

    print(f"Target: {len(sentences)} sentences")
    for i in range(0, len(sentences), CHUNK_SIZE):
        chunk = sentences[i : i + CHUNK_SIZE]

        chunk_results = classifier(chunk, truncation=True, max_length=512, batch_size=CHUNK_SIZE)
        for sub_idx, res in enumerate(chunk_results):
            val = res['score'] if res['label'] == '1' else -res['score']
            scores.append(val)
            print(f"[{i + sub_idx + 1}/{len(sentences)}] {sentences[i + sub_idx][:30]}... -> {val:.4f}")

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
    
    print(f"Filtering {len(filtered_candidates)} words")
    keyword_weights = {}
    for word, score in filtered_candidates.items():
        # 단어에 모델이 낸 점수가 극단적(0.95 이상)이면 알고있는 단어
        test_res = classifier(word, truncation=True)[0]
        model_confidence = test_res['score']
        # 모델 확신도가 너무 높으면 배제
        if model_confidence > 0.92:
            print(f"Word [{word}] is excluded: Model has confidence")
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

        keyword_weights[word] = round(weight, 4)
        print(f"Enroll [{word}, {weight}]")

    return keyword_weights

def main(sentences):
    print("Loading data..")
    if not sentences:
        print("[!] Fail to load data")
        return
    print("Complete")
    
    print("Loading models..")
    classifier = pipeline("sentiment-analysis", model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis")
    st_model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    print("Complete")

    print("Embedding sentences and carculating centroid..")
    # 의미가 비슷한 문장을 좌표 평면상에서 가까운 거리에 위치
    all_embeddings = st_model.encode(sentences, convert_to_tensor=True)
    # 문장들의 평균 위치인 중심점으로 데이터의 평균 주제를 도출
    dataset_centroid = torch.mean(all_embeddings, dim=0)
    print("Complete")

    print("Getting primary sentiment score..")
    sentence_scores = get_sentence_scores(sentences, classifier)
    print("Complete")

    print("Calculating weights..")
    weights = calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid, classifier)
    print("Complete")
    
    return weights