from soynlp.word import WordExtractor
from soynlp.noun import LRNounExtractor_v2
from soynlp.tokenizer import LTokenizer
from soynlp.normalizer import repeat_normalize

sentences = [
    "이거 킹받네 ㅋㅋㅋㅋㅋㅋㅋㅋ",
    "아니 진짜 ㅋㅎㅋㅎㅋㅎㅋㅎㅋㅎ",
    "이번 주식 장 마감 실화냐? 어이가 없네",
    "주식 투자 너무 어려워요 ㅠㅠㅠㅠㅠㅠ",
    "킹받네 라는 말 요즘 너무 많이 쓰는 듯",
    "실화냐 진짜 대박이다",
    "오늘 점심 메뉴 실화냐? 너무 맛없어"
]

#문장 내 반복 표현 정규화
sentences = [repeat_normalize(s, num_repeats=2) for s in sentences]

# 2. 단어 추출기 학습 (WordExtractor)
# 응집 확률(cohesion)과 브랜칭 엔트로피(entropy)를 계산하여 단어를 찾습니다.
word_extractor = WordExtractor()
word_extractor.train(sentences)
word_scores = word_extractor.extract()

# '킹받네'라는 단어의 점수 확인 예시
if '킹받네' in word_scores:
    print(f"--- '킹받네' 분석 결과 ---")
    print(f"응집도(Cohesion): {word_scores['킹받네'].cohesion_proxy:.4f}")
    print(f"통계적 독립도(Entropy): {word_scores['킹받네'].right_branching_entropy:.4f}\n")

# 3. 명사 추출기 (NounExtractor) - 커뮤니티 용어 핵심 키워드 뽑기
noun_extractor = LRNounExtractor_v2(verbose=False)
nouns = noun_extractor.train_extract(sentences) # 학습과 추출을 동시에

print("--- 추출된 명사 목록 ---")
for noun, score in nouns.items():
    # score.frequency는 빈도수입니다.
    print(f"{noun} (빈도: {score.count})")

# 4. 토크나이징 (LTokenizer)
# 위에서 학습한 점수를 바탕으로 문장을 단어 단위로 쪼갭니다.
scores = {word:score.cohesion_proxy for word, score in word_scores.items()}
tokenizer = LTokenizer(scores=scores)

test_sentence = "오늘 주식 장 마감 실화냐 진짜 킹받네"
print(f"\n--- 토큰화 결과 ---")
print(tokenizer.tokenize(test_sentence))