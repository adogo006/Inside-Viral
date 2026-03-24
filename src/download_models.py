from transformers import AutoTokenizer, AutoModelForSequenceClassification; 
from sentence_transformers import SentenceTransformer; 

def download():
    model_name = "jaehyeong/koelectra-base-v3-generalized-sentiment-analysis"; 
    AutoTokenizer.from_pretrained(model_name); 
    AutoModelForSequenceClassification.from_pretrained(model_name);
    sbert_model = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"; 
    SentenceTransformer(sbert_model);

    print('모든 모델을 다운로드 했습니다!')

if __name__ == '__main__':
    download() 