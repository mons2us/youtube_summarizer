import numpy as np
from tqdm import tqdm
import re
from konlpy.tag import Mecab
import gensim
from gensim.models import Word2Vec, KeyedVectors

# load finetuned word2vec model
w2v_path ="/repo/course/sem21_01/youtube_summarizer/dataset/pretrained_word2vec/finetuned_wv.kv"
w2v_model = KeyedVectors.load(w2v_path)

# define mecab tokenizer
mecab = Mecab()

# define stopwords
stopwords = ['을', '를', '이', '가', '은', '는', '의', '에', '와', '으로', '합니다', '입니다']

# define sentence tokenizer
def get_sent_token(sentence, stopwords = stopwords):
    '''
    tokenize input sentence when given using stopwords
    '''
    sent_token = re.sub('[^가-힣a-z]', ' ', sentence) # 영어 소문자와 한글을 제외한 모든 문자를 제거
    sent_token = mecab.morphs(sent_token) # 토큰화
    sent_token = [word for word in sent_token if not word in stopwords] # 불용어 제거

    return sent_token

def get_sent_embedding(sent_token):
    '''
    get sentence token and returns sentece embedding value
    '''

    tokens = sent_token

    w2v_list = []

    for token in tokens:
        tmp_vec = w2v_model.get_vector(token)
        w2v_list.append(tmp_vec)
        #print(len(w2v_list))

    sent_vec = np.mean(w2v_list, axis = 0)

    return sent_vec