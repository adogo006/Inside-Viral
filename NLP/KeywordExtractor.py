# docker exec -it insideviral_devcontainer-crawler-1 python3 main.py  :: 크롤링 컨테이너에서 크롤링 시작
# docker logs -f insideviral_devcontainer-crawler-1 :: 크롤링 컨테이너 로그 보기
# insideviral_devcontainer-crawler-1 :: 크롤러 컨테이너 이름

from soynlp.word import WordExtractor
from soynlp.normalizer import repeat_normalize
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import torch
import math, re
import time

torch.set_num_threads(2)

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
        score.right_branching_entropy >= 1.0
    }

    print(f"Filtering {len(filtered_candidates)} words")
    keyword_weights = []
    word_list = list(filtered_candidates.keys())
    score_list = list(filtered_candidates.values())

    # 배치 처리 (32개씩)
    for i in range(0, len(word_list), 32):
        chunk_words = word_list[i:i + 32]
        chunk_scores = score_list[i:i + 32]

        # 배치로 모델 호출
        batch_results = classifier(chunk_words, truncation=True, max_length=512)

        for j, word in enumerate(chunk_words):
            score = chunk_scores[j]
            test_res = batch_results[j]
            model_confidence = test_res['score']

            # 모델 확신도가 너무 높으면 이미 모델에 있는 단어로 학습에서 배제
            if model_confidence > 0.92:
                print(f"Word [{word}] is excluded: Model has confidence")
                continue

            # 해당 단어가 포함된 문장 인덱스 추출
            indices = [idx for idx, s in enumerate(sentences) if word in s]
            if not indices:
                continue


            # 감성 증폭 (logarithmic scaling - 상한 제한)
            avg_sent = sum(sentence_scores[idx] for idx in indices) / len(indices)
            sentiment_factor = math.copysign(math.log1p(abs(avg_sent) * 10), avg_sent)

            # 의미론적 중요도
            word_centroid = torch.mean(all_embeddings[indices], dim=0)
            semantic_sim = util.cos_sim(word_centroid, dataset_centroid).item()

            # 신조어(model_confidence가 낮을수록) 가중치 보너스
            novelty_bonus = 2.0 - model_confidence

            # 최종 가중치 공식
            weight = (sentiment_factor * score.cohesion_forward) * (semantic_sim * novelty_bonus)

            # 상한값 설정 (clipping)
            weight = max(min(weight, 10.0), -10.0)

            keyword_weights.append({"word": word, "weight": float(round(weight, 4))})
            print(f"Enroll [{word}, {weight}]")

        time.sleep(0.05)

    return keyword_weights

def main(sentences):
    print("Loading data..")
    if not sentences:
        print("[!] Fail to load data")
        return []
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