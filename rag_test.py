# Retrieval Augmented Generation (RAG)를 이용해서 패치하는 것
# - Retrieval Augmented Generation (RAG)(https://www.promptingguide.ai/kr/techniques/rag) 이용해서 해당 취약점에 매칭되는 CWE(https://cwe.mitre.org/data/definitions/78.html)에 요청해서 외부 지식 소스에 액세스하여 완료하는 언어 모델 기반 시스템을 구축

# 일단 CWE 
# https://cwe.mitre.org/data/definitions/{CWE-ID}.html

from helper_utils import *
from patch_utils import *
import pandas as pd
from bs4 import BeautifulSoup
import requests

'''
CWE 번호와 CodeQL query 매칭
'''
with open('./env/codeql-cwe.txt', 'r') as f:
    parse_data = []
    for line in f.readlines():
        cwe_id, query = line.strip().split('\t')[0], line.strip().split('\t')[3]
        parse_data.append((cwe_id, query))
    # print(parse_data)

    df = pd.DataFrame(parse_data, columns=['CWE-ID', 'CodeQL Query'])
    print(df)
    

def get_cwe_id_from_query(query):
    result = df[df['CodeQL Query'] == query]['CWE-ID'].values
    # 여러개 배열로 뽑기
    return result

'''
CWE 번호로부터 취약점 설명을 가져오기
'''
csv_path = './npm-Dataset-main/CVE-2022-0841/output.csv'
project_path = './npm-Dataset-main/CVE-2022-0841/'

vulnerabilities_dict = parse_codeql_csv('./npm-Dataset-main/CVE-2022-0841/output.csv')
print("Vulnerabilities:")
for vulnerability in vulnerabilities_dict:
    cwe_lists = get_cwe_id_from_query(vulnerability['name'])
    print("-"*50)
    for cwe in cwe_lists:
        print(cwe)
        CWE_ID = cwe.split('-')[-1]
        url = f'https://cwe.mitre.org/data/definitions/{CWE_ID}.html'
        print(url)
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'lxml')
        cwe_description = soup.select(f'#oc_{CWE_ID}_Description > div > div')[0].get_text()
        extended_description = soup.select_one(f'#oc_{CWE_ID}_Extended_Description > div > div').get_text()
        print(cwe_description)
        print('-'*50)
        print(extended_description)
        print('-'*50)
        demonstrative = soup.select_one(f'#oc_{CWE_ID}_Demonstrative_Examples > div > div')
        if demonstrative is not None:
            demonstrative_text = demonstrative.get_text()
            print(demonstrative_text)