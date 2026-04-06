from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        print("Loading model..")
        self.classifier = pipeline(
            "sentiment-analysis", 
            model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
        )

    def analyze(self, sentences, weights):
        # (1) 모델의 기본 예측 (Base Score)
        res = self.classifier(sentences, truncation=True)[0]
        primary_score = res['score'] if res['label'] == '1' else -res['score']
        
        # (2) 가중치 사전을 이용한 점수 보정
        adjustment = 0
        found_words = []

        # 문장에 가중치 사전의 단어가 포함되어 있는지 확인
        for word, weight in weights.items():
            if word in sentences:
                adjustment += weight
                found_words.append(f"{word}({weight})")

        # (3) 최종 점수 계산 (모델 점수 + 보정치)
        final_score = primary_score + adjustment
        
        return {
            "text": sentences,
            "primary_score": round(primary_score, 4),
            "adjustment": round(adjustment, 4),
            "final_score": round(final_score, 4),
            "applied_keywords": found_words
        }

def main(sentences, weights):
    analyzer = SentimentAnalyzer()
    results = []

    for sent in sentences:
        result = analyzer.analyze(sent, weights)
        print(f"Sentence: {result['text']}")
        print(f"Primary score: {result['primary_score']}")
        print(f"Adjustment: {result['adjustment']} (Applied keywords: {result['applied_keywords']})")
        print(f"Final score: {result['final_score']}")
        print("-" * 50)

        results.append({
            "word_id": sent.id,
            "word_content": sent.wordContent,
            "final_score": result['final_score']
        })

    return results