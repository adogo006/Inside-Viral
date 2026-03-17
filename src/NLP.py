from transformers import pipeline
import pandas as pd

#crawling.py에서 Word={gellID, time, wordContent, sentiment}를 리스트로 전달
#wordList = Word

#sentiment 파이프라인 생성, 적정 모델 필요
classifier = pipeline("sentiment-analysis", model="jaehyeong/koelectra-base-v3-generalized-sentiment-analysis")

#sentences = wordList.wordContent
sentences = ["input any text here"]

ret = classifier(sentences)
for i in range(len(sentences)):
    print(f"\n\"{sentences[i]}\"\nlabel: {ret[i]['label']}\tscore: {ret[i]['score']:.4f}")