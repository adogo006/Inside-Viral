from transformers import pipeline
import pandas as pd

MODEL = "jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"
classifier = pipeline("sentiment-analysis", model=MODEL)

sentences = []

ret = classifier(sentences)
for i in range(len(sentences)):
    print(f"\n\"{sentences[i]}\"\nlabel: {ret[i]['label']}\tscore: {ret[i]['score']:.4f}")
    

# ELECTRA 모델은 인터넷 댓글 기반 학습이라 커뮤 용어를 이해하는 것이 뛰어남
# 하지만 여전히 커뮤니티 용어가 특정 상황에서는 어떤 의미인지를 인식할 수 없음

# ex) 반대의 문장을 비슷한 의미로 인식, 반어를 모르고 "ㅋㅋ"를 긍정의 의미로 해석
# "숏충이들 멸망ㅋㅋ" => label: 1, score: 0.6328
# "롱숭이들 멸망ㅋㅋ" => label: 1, score: 0.5628

# 직접 키워드를 추출해서 가중치를 주는 식의 전처리가 필수불가결
# 다시 soynlp를 사용하여 키워드를 추출하는 과정이 필요할 듯 하다

# 아니면 LLM 모델을 사용하는 것도 있다 (Llama-3 / Gemini API) 근데 굳이?

# soynlp로 커뮤니티 게시글들을 학습한 이후 추출한 키워드에 자동으로 가중치를 지정
# transformers로 문장의 sentiment(score)를 도출할 때 키워드가 있다면 가중치 연산
# 학습해서 키워드를 추출하는 프로그램이랑 문장의 score를 도출하는 프로그램을 분리