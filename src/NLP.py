from transformers import pipeline
import pandas as pd

#crawling.py에서 Word={gellID, time, wordContent, sentiment}를 리스트로 전달
#wordList = Word

#sentiment 파이프라인 생성, KR-BERT 모델 사용
classifier = pipeline("sentiment-analysis", model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis")

#sentences = wordList.wordContent
sentences = ["트럼프 참 잘하는 짓이다"]

ret = classifier(sentences)
for i in range(len(sentences)):
    print(f"\n\"{sentences[i]}\"\nlabel: {ret[i]['label']}\tscore: {ret[i]['score']:.4f}")