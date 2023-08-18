import os
os.environ['DATA_DIR'] = 'data' # ты указываешь путь к своей папке
# Для данных
import pandas as pd
import numpy as np
import json
import re
import os

# Для плюшек 
import sklearn as sk
import nltk
from nltk.corpus import stopwords

# Для красоты
import seaborn as sns
from pprint import pprint
import typing

nltk.download("stopwords") # поддерживает удаление стоп-слов
nltk.download('punkt') # делит текст на список предложений
nltk.download('wordnet') # проводит лемматизацию

def get_hr(folder: str, hr_num: str) -> np.array:
    with open(f'{os.environ["DATA_DIR"]}/{folder}/{hr_num}.npy', "rb") as f:
        return np.load(f, allow_pickle=True)


def flatten_list(lst: typing.List[any]) -> typing.List[any]:
    new_lst = []
    for elem in lst:
        if isinstance(elem, list):
            new_lst.extend(flatten_list(elem))
        else:
            new_lst.append(elem)
            
    return new_lst

def global_info(meta: pd.DataFrame):
    for column in meta.columns:
        print(f'Column name: {column} {round(meta[column].notna().sum() / len(meta) * 100, 2)}%')
        print(meta[column].value_counts() if len(meta[column].unique()) < 14 else f'so much unique values\n{meta[column].describe()}')
        print()

ecg_columns = ['report', 'scp_codes', 'heart_axis', 'infarction_stadium1', 'infarction_stadium2', 'validated_by', 
'second_opinion', 'initial_autogenerated_report', 'validated_by_human', 'baseline drift', 'static_noise', 'burst_noise', 'electrodes_problems', 
'extra_beats']

meta = pd.read_csv(f'{os.environ["DATA_DIR"]}/test/test_meta.csv')
diagnosis = pd.read_csv(f'{os.environ["DATA_DIR"]}/train/train_gts.csv')

useless_columns = ['ecg_id', 'patient_id', 'nurse', 'site', 'device', 'recording_date', 'filename_lr', 'filename_hr', 'report']
meta.drop(columns=useless_columns, inplace=True)

strange_columns = ['age', 'sex', 'pacemaker', 'group']

empty_columns = ['height', 'weight', 'heart_axis']
meta.drop(columns=empty_columns, inplace=True)

meta.drop(meta[meta['electrodes_problems'].notna()].index, inplace=True)
meta.drop(columns=['electrodes_problems'], inplace=True)
#meta.drop(1514, inplace=True) # Хех пока

meta = meta.reset_index(drop=True)

noise_types = ['I', 'II', 'III', 'AVR', 'AVL', 'AVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

def str_to_noise(s: str) -> typing.List[str]:
    if not isinstance(s, str):
        return []
    noises = []
    
    if 'alles' in s: # alles - all
        return noise_types
    
    vnable = False
    for elem in s.split(','):
        elem = elem.strip(',- ').upper()
        if not elem:
            continue
        if 'V' in elem and 'A' not in elem:
            vnable = True
        else:
            if vnable and elem in map(str, range(1, 7)):
                elem = 'V' + elem
        if '-' in elem:
            elem = elem.split('-')
            if 'V' in elem[0] and 'V' not in elem[1]:
                elem[1] = 'V' + elem[1]
            noises.extend(noise_types[noise_types.index(elem[0].strip(',- ')):noise_types.index(elem[1].strip(',- '))+1])
        else:
            noises.append(elem)
            
    return noises

def scp_convert(s: str) -> typing.Dict[str, int]:
    return json.loads(s.replace("'", '"'))

meta['baseline_drift'] = meta['baseline_drift'].apply(str_to_noise)
meta['static_noise'] = meta['static_noise'].apply(str_to_noise)
params = set(flatten_list([list(eval(codes).keys()) for codes in meta['scp_codes'].unique().tolist()]))
meta['scp_codes'] = meta['scp_codes'].apply(scp_convert)

for elem in noise_types:
    meta[f'static_noise_{elem}'] = False
    for id, row in meta.iterrows():
        meta.loc[id, f'static_noise_{elem}'] = bool(elem in row['static_noise'])

for elem in noise_types:
    meta[f'baseline_drift_{elem}'] = False
    for id, row in meta.iterrows():
        meta.loc[id, f'baseline_drift_{elem}'] = bool(elem in row['baseline_drift'])

for elem in params:
    meta[f'scp_{elem}'] = meta['scp_codes'].apply(lambda x: x.get(elem))

meta.drop(columns=['baseline_drift', 'static_noise', 'scp_codes'], inplace=True)

str_columns = ['infarction_stadium1', 'infarction_stadium2', 'burst_noise', 'pacemaker', 'extra_beats']

meta = pd.get_dummies(meta, columns=str_columns, dtype=bool)