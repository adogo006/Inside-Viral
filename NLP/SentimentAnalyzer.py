import json, os
from transformers import pipeline

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(BASE_PATH, 'weights.json')

class SentimentAnalyzer:
    def __init__(self):
        print("모델 로드 중...")
        self.classifier = pipeline(
            "sentiment-analysis", 
            model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
        )
        
        # 가중치 사전(weights.json) 로드
        self.custom_weights = self._load_weights()
        print(f"가중치 사전 로드 완료: {len(self.custom_weights)}개 단어")

    def _load_weights(self):
        if os.path.exists(WEIGHTS_PATH):
            with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def analyze(self, text):
        # (1) 모델의 기본 예측 (Base Score)
        res = self.classifier(text, truncation=True)[0]
        base_score = res['score'] if res['label'] == '1' else -res['score']
        
        # (2) 가중치 사전을 이용한 점수 보정
        adjustment = 0
        found_words = []

        # 문장에 가중치 사전의 단어가 포함되어 있는지 확인
        for word, weight in self.custom_weights.items():
            if word in text:
                adjustment += weight
                found_words.append(f"{word}({weight})")

        # (3) 최종 점수 계산 (모델 점수 + 보정치)
        final_score = base_score + adjustment
        
        return {
            "text": text,
            "base_score": round(base_score, 4),
            "adjustment": round(adjustment, 4),
            "final_score": round(final_score, 4),
            "applied_keywords": found_words
        }

def main():
    analyzer = SentimentAnalyzer()
    
    # 테스트 문장들
    test_sentences = []
    with open("db_content.txt", 'r', encoding='utf-8') as f:
        test_sentences = f.read().splitlines()
    
    print("\n" + "="*50)
    for sent in test_sentences:
        result = analyzer.analyze(sent)
        print(f"문장: {result['text']}")
        print(f"기본 점수: {result['base_score']}")
        print(f"보정치: {result['adjustment']} (적용된 단어: {result['applied_keywords']})")
        print(f"최종 점수: {result['final_score']}")
        
        # 결과 해석
        status = "긍정" if result['final_score'] > 0 else "부정"
        print(f"결론: 이 문장은 최종적으로 [{status}]로 판단됩니다.")
        print("-" * 50)