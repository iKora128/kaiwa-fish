from transformers import AutoTokenizer, AutoModelForSequenceClassification, LukeConfig
import torch
import MeCab
import re
import time

EMOJI_PATTERN = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)

def remove_emoji(text):
    return EMOJI_PATTERN.sub(r'', text)

def split_sentence(text):
    text = remove_emoji(text)
    tagger = MeCab.Tagger()
    parsed = tagger.parse(text)
    words = [line.split('\t')[0] for line in parsed.split('\n') if line][:-1]
    sentence_endings = {'.', '！', '？', '。'}
    
    sentences = []
    current_sentence = []
    
    for word in words:
        if word in sentence_endings:
            current_sentence.append(word)
            sentences.append(''.join(current_sentence).strip())
            current_sentence = []
        else:
            current_sentence.append(word)
    
    if current_sentence:
        sentences.append(''.join(current_sentence).strip())
    
    return sentences


class SentimentAnalyzer:
    """
    https://huggingface.co/Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime 
    [喜び, 悲しみ, 期待, 驚き, 怒り, 恐れ, 嫌悪, 信頼] の8つの感情ラベルに分類するモデルを使用
    emotion_mappingではフロントが期待している感情ラベルに変換している
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime")
        config = LukeConfig.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', output_hidden_states=True)
        self.model = AutoModelForSequenceClassification.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', config=config)
        self.model.to(self.device)
        
        self.emotion_mapping = {
            0: 2,  # joy -> happy
            1: 3,  # sadness -> sad
            2: 1,  # anticipation -> relax
            3: 5,  # surprise -> C_surprised
            4: 4,  # anger -> angry
            5: 9,  # fear -> C_shock
            6: 6,  # disgust -> C_jitome
            7: 8,  # trust -> C_tere
        }
        
    def analyze(self, input: str) -> int:
        max_seq_length = 512
        token = self.tokenizer(input,
                               truncation=True,
                               max_length=max_seq_length,
                               padding="max_length",
                               return_tensors="pt")
        
        input_ids = token['input_ids'].to(self.device)
        attention_mask = token['attention_mask'].to(self.device)
        
        with torch.no_grad():
            output = self.model(input_ids, attention_mask=attention_mask)
        
        max_index = torch.argmax(output.logits).item()
        mapped_emotion = self.emotion_mapping.get(max_index, 0)  # デフォルトは0 (normal)
        
        return mapped_emotion

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    start_time = time.time()
    result = analyzer.analyze("すごく楽しかった。また行きたい。")
    end_time = time.time()
    print(f"推論時間: {end_time - start_time} seconds")
    print(f"感情ラベル: {result}")
