from transformers import pipeline
import torch
import time
import re

torch.set_num_threads(2)

class SentimentAnalyzer:
    def __init__(self):
        print("Loading model..")
        self.classifier = pipeline(
            "sentiment-analysis", 
            model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
        )

    def analyze_batch(self, sentences, weights, batch_size=32):
        results = []
        for i in range(0, len(sentences), batch_size):
            chunk = sentences[i:i + batch_size]
            texts = []
            for sent in chunk:
                if hasattr(sent, "wordContent"):
                    texts.append(sent.wordContent)
                else:
                    texts.append(str(sent))

            # 배치로 모델 호출
            batch_results = self.classifier(texts, truncation=True, max_length=512)

            for j, res in enumerate(batch_results):
                sentence_text = texts[j]
                primary_score = res['score'] if res['label'] == '1' else -res['score']

                # 가중치 보정 (단어 경계 매칭)
                adjustment = 0
                found_words = []
                for word, weight in weights.items():
                    if re.search(r'\b' + re.escape(word) + r'\b', sentence_text):
                        adjustment += weight
                        found_words.append(f"{word}({weight})")

                # 최종 sentiment 점수 계산
                final_score = primary_score + adjustment

                print(f"[{i + j + 1}/{len(sentences)}] {sentence_text[:30]}... -> {final_score:.4f}")

                results.append({
                    "text": sentence_text,
                    "primary_score": round(primary_score, 4),
                    "adjustment": round(adjustment, 4),
                    "final_score": round(final_score, 4),
                    "applied_keywords": found_words
                })

                time.sleep(0.05)

        return results

def main(sentences, weights):
    analyzer = SentimentAnalyzer()
    batch_results = analyzer.analyze_batch(sentences, weights)
    results = []

    print(f"Total {len(sentences)} sentences")
    for idx, result in enumerate(batch_results):
        sent = sentences[idx]
        print(f"[{idx + 1}/{len(sentences)}] Sentence: {result['text']}")
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