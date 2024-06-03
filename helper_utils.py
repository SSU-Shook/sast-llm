'''
sast_llm.py 파일에서 활용하는
SAST의 기능 자체와는 직접적인 관련이 적은
유틸리티 함수 모음
'''

import os
import time
import json
import glob
import difflib
import re
from env import settings
import tempfile
import csv
import uuid
import shutil
import pandas as pd
from bs4 import BeautifulSoup
import requests




def generate_diff(text1, text2):
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    diff = []
    for line in difflib.unified_diff(lines1, lines2):
        diff.append(line)

    return '\n'.join(diff)




def generate_directory_name():
    return str(uuid.uuid4())


def get_file_name_from_path(file_path):
    return os.path.basename(file_path)





def get_js_file_list(directory_path):
    '''
    특정 경로의 디렉터리에서 .js 파일 리스트를 재귀적으로 탐색하여 반환한다.
    '''
    file_list = []
    for path in glob.iglob(f'{directory_path}/**/*.js', recursive=True):
        file_list.append({"filename": os.path.basename(path), "path":path})
    return file_list





def get_file_list_from_path_list(path_list):
    '''
    특정 경로의 디렉터리에서 .js 파일 리스트를 재귀적으로 탐색하여 반환한다.
    '''
    file_list = []
    for path in path_list:
        file_list.append({"filename": os.path.basename(path), "path":path})
    return file_list





def save_js_file_list_to_jsonl(file_list, jsonl_file_path):
    '''
    file_list를 jsonl 파일로 저장한다.
    '''
    with open(jsonl_file_path, "w") as f:
        for file in file_list:
            f.write(json.dumps(file) + "\n")




def get_full_path(base_path, file_path):
    if file_path.startswith(base_path):
        return file_path
    
    if file_path.startswith("/"):
        file_path = './' + file_path

    print(f'base_path: {base_path}, file_path: {file_path}')
    return os.path.abspath(os.path.join(base_path, file_path))





def extract_directory_name(directory_path):
    '''
    디렉터리 경로로부터 디렉터리 이름을 추출하여 반환한다.
    '''
    return os.path.basename(directory_path)



def reverse_dict(dictionary):
    return {value: key for key, value in dictionary.items()}



'''
copy_source_code_files 함수
전체 폴더에서 취약점이 존재하는 파일과 상위 폴더만 복사하는 함수 
이 함수는 원본 코드의 경로와, 이에 대응하는 복사본 코드의 경로를 반환한다.
'''
def copy_source_code_files(project_path, project_uuid, vulnerabilities_dict_by_file):
    '''
    취약점이 존재하는 파일과 상위 폴더만 복사한다.
    '''

    '''
    복사할 때 유의할 점
    폴더 이름이 같은 프로젝트를 여러 번 복사할 수도 있다.
    이는 모두 서로 다른 프로젝트이므로 별도의 폴더에 저장해야한다.
    이를 간단히 구현하기 위하여
    comment_added_codes/임의문자열/프로젝트이름/**
    형식으로 복사한다.
    임의 문자열은 어떻게 정할까? 이를 위하여 generate_directory_name 함수를 만들었다.


    내가 원하는 대로 구현하려면 모든 파일 경로는 절대경로로 저장되어야 한다.
    이를 위한 점검 단계를 거치자.
    '''

    original_path_copied_path_dict = dict()

    original_directory_name = extract_directory_name(project_path)
    copied_directory_name = project_uuid

    copied_directory_path = os.path.join("comment_added_codes", copied_directory_name)
    copied_directory_path = os.path.join(copied_directory_path, original_directory_name)

    os.makedirs(copied_directory_path)

    original_path_copied_path_tuple_list = list()
    for file_path in vulnerabilities_dict_by_file.keys():
        file_relative_path = os.path.relpath(file_path, project_path)
        copied_file_path = get_full_path(copied_directory_path, file_relative_path) #여기가 절대경로인게 문제
        os.makedirs(os.path.dirname(copied_file_path), exist_ok=True)
        shutil.copy(file_path, copied_file_path)

        original_path_copied_path_dict[file_path] = copied_file_path
        
        
    return original_path_copied_path_dict



def get_patched_code_save_directory(project_path, directory_name=generate_directory_name()):
    '''
    패치된 코드를 저장할 디렉터리를 생성하고 반환한다.
    '''
    
    base_directory_name = os.path.basename(project_path)
    patched_code_save_directory = os.path.join("patched_codes", directory_name)
    patched_code_save_directory = os.path.join(patched_code_save_directory, base_directory_name)
    os.makedirs(patched_code_save_directory)
    return patched_code_save_directory



def get_relative_path(project_path, code_path):
    '''
    project_path로부터 code_path까지의 상대 경로를 구한다.
    '''
    return os.path.relpath(code_path, project_path)


def get_cwe_description(cwename):
    '''
    CWE 번호와 CodeQL query 매칭
    '''

    command = 'This is a description of the vulnerability information. Please patch your code with the following.\n'

    with open('./env/codeql-cwe.txt', 'r') as f:
        parse_data = []
        for line in f.readlines():
            cwe_id, query = line.strip().split('\t')[0], line.strip().split('\t')[3]
            parse_data.append((cwe_id, query))
        # print(parse_data)

        df = pd.DataFrame(parse_data, columns=['CWE-ID', 'CodeQL Query'])
        # print(df)
        
    def get_cwe_id_from_query(query):
        result = df[df['CodeQL Query'] == query]['CWE-ID'].values
        # 여러개 배열로 뽑기
        return result

    '''
    CWE 번호로부터 취약점 설명을 가져오기
    '''
    
    # csv_path = './npm-Dataset-main/CVE-2022-0841/output.csv'
    # project_path = './npm-Dataset-main/CVE-2022-0841/'

    # vulnerabilities_dict = parse_codeql_csv('./npm-Dataset-main/CVE-2022-0841/output.csv')
    # print("Vulnerabilities:")


    # for vulnerability in vulnerabilities_dict:
    # cwe_lists = get_cwe_id_from_query(vulnerability['name'])
    cwe_lists = get_cwe_id_from_query(cwename)
    # print("-"*50)
    for cwe in cwe_lists:
        # print(cwe)
        CWE_ID = cwe.split('-')[-1]
        url = f'https://cwe.mitre.org/data/definitions/{CWE_ID}.html'
        # print(url)
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'lxml')
        cwe_description = soup.select(f'#oc_{CWE_ID}_Description > div > div')[0].get_text()
        extended_description = soup.select_one(f'#oc_{CWE_ID}_Extended_Description > div > div').get_text()
        # print(cwe_description)
        # print('-'*50)
        # print(extended_description)
        # print('-'*50)
        demonstrative = soup.select_one(f'#oc_{CWE_ID}_Demonstrative_Examples > div > div')
        if demonstrative is not None:
            demonstrative_text = demonstrative.get_text()
            # print(demonstrative_text)

        command += '[*]' + cwe + ' information:' + '\n'
        command += '- CWE Description: ' + cwe_description + '\n'
        command += '- Extended Description: ' + extended_description + '\n'
        command += '- Demonstrative Text: ' + demonstrative_text + '\n'

    return command