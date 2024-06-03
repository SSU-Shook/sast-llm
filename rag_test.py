# Retrieval Augmented Generation (RAG)를 이용해서 패치하는 것
# - Retrieval Augmented Generation (RAG)(https://www.promptingguide.ai/kr/techniques/rag) 이용해서 해당 취약점에 매칭되는 CWE(https://cwe.mitre.org/data/definitions/78.html)에 요청해서 외부 지식 소스에 액세스하여 완료하는 언어 모델 기반 시스템을 구축

# 일단 CWE 
# https://cwe.mitre.org/data/definitions/{CWE-ID}.html

from helper_utils import *
from patch_utils import *
import pandas as pd
# from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
import requests
from lxml import etree


# csv에서 취약점 name 빼온 다음에, CWE ID 매칭시키기

# 취약점 이름을 받아서 CWE ID를 반환하는 함수

csv_path = './npm-Dataset-main/CVE-2022-0841/output.csv'
project_path = './npm-Dataset-main/CVE-2022-0841/'

vulnerabilities_dict = parse_codeql_csv('./npm-Dataset-main/CVE-2022-0841/output.csv')
print("Vulnerabilities:")
for vulnerability in vulnerabilities_dict:
    print(vulnerability)
print("-"*50)

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

cwe_lists = get_cwe_id_from_query('Indirect uncontrolled command line')

for cwe in cwe_lists:
    print(cwe)
    CWE_ID = cwe.split('-')[-1]
    url = f'https://cwe.mitre.org/data/definitions/{CWE_ID}.html'
    print(url)
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'lxml')
    dom = etree.HTML(str(soup))
    cwe_description = dom.xpath(f'//*[@id="oc_{CWE_ID}_Description"]/div/div/text()')[0]
    extended_description = soup.select_one(f'#oc_{CWE_ID}_Extended_Description > div > div').get_text()
    print(cwe_description)
    print('-'*50)
    print(extended_description)

    print('-'*50)
    # Demonstrative Examples
    demonstrative = soup.select_one(f'#oc_{CWE_ID}_Demonstrative_Examples > div > div')
    if demonstrative is not None:
        demonstrative_text = demonstrative.get_text()
        print(demonstrative_text)

    


# print(cwe_dict)

# for key, value in cwe_dict.items():
#     if key == 'Indirect uncontrolled command line':
#         print(key, value)


# vulnerabilities_dict_by_file = dict()
# for vulnerability in vulnerabilities_dict:
#     source_absolute_path = get_full_path(project_path, vulnerability['path'])
#     if source_absolute_path in vulnerabilities_dict_by_file:
#         vulnerabilities_dict_by_file[source_absolute_path].append(vulnerability)
#     else:
#         vulnerabilities_dict_by_file[source_absolute_path] = [vulnerability]
# print("Vulnerabilities by file:")
# for key, value in vulnerabilities_dict_by_file.items():
#     print(key, value)
# print("-"*50)