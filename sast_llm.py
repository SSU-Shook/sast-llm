import os
import time
import json
import glob
import difflib
import re
from env import settings
from openai import OpenAI
import tempfile
import instructions
import csv
import uuid
import shutil

from helper_utils import *
from patch_utils import *


'''
Todo
# - .js filename list & path to .jsonl file
# - Upload the codebase
- Few-shot prompting with example codes
- query the model for the output
    - match code style
    - profiling the code style (e.g. tabWidth, semi, etc.)
- save the output to a file (e.g. security patch comments, etc.)
- refactoring the code
- testing the code (diffing, performance, etc.)
- translate english to korean or extract comment to korean
- 클래스화
'''



# 스크립트 파일의 절대 경로를 가져옵니다.
script_directory = os.path.abspath(os.path.dirname(__file__))

# 현재 작업 디렉터리를 스크립트가 있는 디렉터리로 변경합니다.
os.chdir(script_directory)

# 변경된 작업 디렉터리를 확인합니다.
print("현재 작업 디렉터리:", os.getcwd())



try:
    client = OpenAI(
        api_key=settings.LLM_API_KEY['openai'],
    )
except:
    print("OpenAI() failed")
    
try:
    os.system("rm filelist.jsonl")
except:
    pass




def create_attachments_list(file_id_list):
    '''
    파일 id 리스트를 입력받아 attachments 리스트를 생성한다.
    '''
    attachments_list = []
    for file in file_id_list:
        attachments_list.append({"file_id": file, "tools": [{"type": "code_interpreter"}]}) #code_interpreter, file_browser   둘 다 패치 코드 특수문자 깨짐 증상
    return attachments_list    



def check_status(run_id,thread_id):
    '''
    run의 상태를 반환한다.
    '''
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id,
    )
    if run.status == 'failed':
        print(f"Failed: {run.last_error.code} {run.last_error.message}")
        raise Exception("Failed")
    return run.status



def upload_file(file_path):
    '''
    파일 하나를 클라이언트에 업로드하고, 업로드된 파일 객체를 반환한다.
    '''
    with open(file_path, "rb") as f:
        file = client.files.create(
            file=f,
            purpose = 'assistants'
        ) # 파일 업로드 하면 언제까지 유지가 되는지.... : 안 지우면 유지되는 듯
        print(file)
    return file






def get_assistant_id(assistant_type):
    '''
    어시스턴트를 아이디를 반환한다.

    profile_assistant: 코딩 컨벤션 프로파일링을 위한 assistant
    예제 코드 10개를 입력하여(10개인 이유는 API의 한계... 더 가능할 시 수정), 코딩 컨벤션을 분석한 결과를 반환한다.

    patch_assistant: 취약점 패치를 위한 assistant
    profile_assistant가 반환한 코딩 컨벤션 분석 결과와, 취약 소스코드를 입력하여 코드를 패치한다.

    explain_assistant: 취약점 패치 설명을 위한 assistant
    취약점이 존재하는 코드 파일과, 취약점 패치 후의 코드 파일을 입력하여, 취약점과 패치 내용에 대한 설명을 반환받는다.
    '''

    if settings.ASSISTANT_ID[assistant_type] is None: # 만약 LLM_API_KEY 딕셔너리에 assistant id가 없다면 새로운 assistant를 만든다.
        raise Exception("Patch assistant is not defined.")
        
    return settings.ASSISTANT_ID[assistant_type]




def upload_files(file_list):
    '''
    파일 리스트를 입력받아 파일을 업로드하고, 업로드된 파일의 id 리스트를 반환한다.
    '''
    file_id_list = []
    for file in file_list:
        temp_file_path = preprocess_code(file['path'])
        print(f'[*] {temp_file_path}')
        assistant_file_object = upload_file(temp_file_path)
        file_id_list.append(assistant_file_object.id)
        os.remove(temp_file_path)
    return file_id_list




def download_file(file_id, download_path):
    '''
    파일 id를 입력받아, 다운로드 경로에 파일을 다운로드한다.
    '''
    file_path = download_path
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True) # 경로상의 디렉터리가 없으면 생성

    with open(download_path, "wb") as f:
        content = client.files.content(file_id).read()
        print(content)
        f.write(content)
    return download_path




def profile_code_style(project_path, zero_shot_cot=False):
    '''
    프로젝트 경로로부터 .js 파일 리스트 뽑기
    '''
    file_list = get_js_file_list(project_path)
    print("File list:")
    print(file_list)
    print('-'*50)



    '''
    .js 파일들을 client에 업로드
    '''
    file_id_list = upload_files(file_list)
    print("Uploaded file id list:")
    print(file_id_list)
    print('-'*50)



    '''
    코딩 스타일 프로파일을 위한 thread 생성
    '''
    profile_thread  = client.beta.threads.create() # 대화 세션 정도로 이해하면 될 듯



    '''
    코딩 스타일 추출 메시지에 첨부할 메시지 리스트 생성
    '''
    codebase_example_attachments_list = create_attachments_list(file_id_list)



    '''
    프로파일 생성 요청 메시지들을 스레드에 추가
    '''
    prompt = instructions.prompt_code_style_analysis
    if zero_shot_cot == True:
        prompt += '\n' + "Let's think step by step."

    if zero_shot_cot == "explain1":
        prompt += '\n' + "First, the process of deriving the answer is explained in detail, and then the answer to the request is printed at the end."

    message = client.beta.threads.messages.create(
        thread_id=profile_thread.id,
        role="user",
        content=prompt,
        attachments=codebase_example_attachments_list,
    )



    '''
    스레드 실행
    '''
    profile_run = client.beta.threads.runs.create(
        thread_id=profile_thread.id,
        assistant_id=get_assistant_id('profile_assistant')
    )



    start_time = time.time()


    status = check_status(profile_run.id, profile_thread.id)
    while status != 'completed':
        time.sleep(1)
        status = check_status(profile_run.id, profile_thread.id)



    elapsed_time = time.time() - start_time
    print("Elapsed time: {} minutes {} seconds".format(int((elapsed_time) // 60), int((elapsed_time) % 60)))
    print(f'Status: {status}')
    print('-'*50)


    '''
    thread의 메시지 목록 가져오기
    '''
    messages = client.beta.threads.messages.list(
        thread_id=profile_thread.id
    )


    '''
    llm의 프로파일 결과 출력
    '''
    llm_profile_result = messages.data[0].content[0].text.value
    print(llm_profile_result)
    print('-'*50)


    '''
    llm의 출력 결과에서 코딩 컨벤션 프로파일(json 형태)만 추출
    '''
    print("Code style profile:")
    extracted_codes_from_llm_profile_result = extract_code(llm_profile_result)
    extracted_json_codes_from_llm_profile_result = [code[1] for code in extracted_codes_from_llm_profile_result if code[0] == 'json']
    

    for code in extracted_json_codes_from_llm_profile_result:
        if code[0] == 'json':
            print(code[1])
    print('-'*50)


    return extracted_json_codes_from_llm_profile_result[-1] # json 문자열 형식으로 반환





'''
프로젝트 경로와 codeql csv 파일 경로를 입력받아 취약점을 패치함
원래 파일과 패치된 파일의 경로를 원소로 가지는 튜플로 이루어진 배열 반환
'''
def patch_vulnerabilities(project_path, codeql_csv_path, code_style_profile=None, zero_shot_cot=False, rag=False):
    '''
    codeql csv 파일을 파싱하여 취약점 정보를 추출한다.
    '''
    vulnerabilities_dict = parse_codeql_csv(codeql_csv_path)
    print("-"*50)
    print("Vulnerabilities:")
    for vulnerability in vulnerabilities_dict:
        print(vulnerability)
    print("-"*50)

    
    
    '''
    같은 파일에 대한 취약점들끼리 모은다.
    {(파일경로, [취약점1, 취약점2, ...]), ...}
    '''
    vulnerabilities_dict_by_file = dict()
    for vulnerability in vulnerabilities_dict:
        source_absolute_path = get_full_path(project_path, vulnerability['path'])
        if source_absolute_path in vulnerabilities_dict_by_file:
            vulnerabilities_dict_by_file[source_absolute_path].append(vulnerability)
        else:
            vulnerabilities_dict_by_file[source_absolute_path] = [vulnerability]
    print("Vulnerabilities by file:")
    for key, value in vulnerabilities_dict_by_file.items():
        print(key, value)
    print("-"*50)

    

    '''
    파일별로 주석으로 취약점 정보를 추가한다.
    이를 위해서는 기존 파일을 복사해서 어딘가에 저장해야 한다.
    어디에 저장할까?
    comment_added_codes 폴더를 추가하자. (해당 폴더는 .gitignore에 추가)

    comment_source_code 함수
    이 함수는 코드 파일의 경로를 입력받아서 취약점 정보를 주석으로 추가한다.

    '''

    project_uuid = generate_directory_name()
    original_path_copied_path_dict = copy_source_code_files(project_path, project_uuid, vulnerabilities_dict_by_file)
    print(original_path_copied_path_dict)

    for code_path, vulnerabilities in vulnerabilities_dict_by_file.items():
        comment_source_code(original_path_copied_path_dict[code_path], vulnerabilities)
        with open(original_path_copied_path_dict[code_path], 'r', encoding='UTF8') as file:
            print(file.read())
   

    code_patch_result = dict()
    code_patch_result['patched_files'] = dict()
    '''
    파일별로 message를 생성하고 thread를 생성하여 취약점을 패치한다.
    패치된 파일을 다운로드하고, 특정 경로에 patched_원본파일이름 으로 저장한다.
    code_patch_result {'patched_files':{원본경로:패치된파일경로, ...}, 'vulnerabilities_by_file':vulnerabilities_dict_by_file} 반환
    '''
    patched_project_save_path = get_patched_code_save_directory(project_path, project_uuid)
    for code_path, vulnerabilities in vulnerabilities_dict_by_file.items():
        patch_thread = client.beta.threads.create()

        fild_id_list = upload_files(get_file_list_from_path_list([original_path_copied_path_dict[code_path]]))
        attachments_list = create_attachments_list(fild_id_list)
        
        # print(f'[*] DEBUG : {vulnerabilities}, {vulnerabilities[0]}, {vulnerabilities[0]["name"]}')

        # if rag:
        #     prompt = instructions.prompt_patch_vulnerabilities + \
        #         get_cwe_description(vulnerabilities[0]['name'])
        # else:
        #     prompt = instructions.prompt_patch_vulnerabilities

        # print(f'[DEBUG] len(prompt) : {len(prompt)}')



        '''
        rag 프롬프트 수행
        '''
        if rag:
            print('[*] RAG Prompt')
            rag_prompt = 'This is a description of vulnerability information. Learn the content.\n' + \
                '**Do nothing in response to this command**' + get_cwe_description(vulnerabilities[0]['name'])
        
            print(f'[DEBUG] len(rag_prompt) : {len(rag_prompt)}')

            message = client.beta.threads.messages.create(
                thread_id=patch_thread.id,
                role="user",
                content=rag_prompt,
            )

            patch_run = client.beta.threads.runs.create(
                thread_id=patch_thread.id,
                assistant_id=get_assistant_id('rag_assistant')
            )

            start_time = time.time()

            status = check_status(patch_run.id, patch_thread.id)
            while status != 'completed':
                time.sleep(1)
                status = check_status(patch_run.id, patch_thread.id)

            elapsed_time = time.time() - start_time
            print("Elapsed time: {} minutes {} seconds".format(int((elapsed_time) // 60), int((elapsed_time) % 60)))
            print(f'Status: {status}')
            print('-'*50)

        '''
        패치 프롬프트 수행
        '''

        prompt = instructions.prompt_patch_vulnerabilities

        message = client.beta.threads.messages.create(
            thread_id=patch_thread.id,
            role="user",
            content=prompt,
            attachments=attachments_list,
        )

        patch_run = client.beta.threads.runs.create(
            thread_id=patch_thread.id,
            assistant_id=get_assistant_id('patch_assistant')
        )

        start_time = time.time()

        status = check_status(patch_run.id, patch_thread.id)
        while status != 'completed':
            time.sleep(1)
            status = check_status(patch_run.id, patch_thread.id)

        elapsed_time = time.time() - start_time
        print("Elapsed time: {} minutes {} seconds".format(int((elapsed_time) // 60), int((elapsed_time) % 60)))
        print(f'Status: {status}')
        print('-'*50)

        messages = client.beta.threads.messages.list(
            thread_id=patch_thread.id
        )



        for message in messages:
            print(message.content[0].text.value)
            print('*'*50)
        print('-'*50)


        for message in messages:
            print(message)
            print(message.attachments)
            print('*'*50)
        print('-'*50)


        llm_patch_result = messages.data[0].content[0].text.value
        print(llm_patch_result)
        print('-'*50)




        # https://platform.openai.com/docs/api-reference/files/retrieve-contents
        '''
        LLM이 응답한 파일을 다운받아야 한다.
        다운받는 방법은 위 링크에서 확인할 수 있다.
        그렇다면 다운받은 다음에 어디에 저장할까?
        patched_codes 폴더에 uuid 값으로 폴더를 만든 다음에, 그 안에 코드베이스와 같은 디렉터리 구조를 만들고 원본 파일 이름으로 저장하자.
        그리고 다음과 같이 반환하자
        {
            'patched_file_path': [
                {원본파일경로: 패치된파일경로},
                ...
            ],
            'vulnerabilities_by_file': vulnerabilities_dict_by_file_name
        }

        확인 결과, 앞쪽 인덱스가 최신 결과이다. 
        따라서 가장 앞에 있는 첨부파일을 찾아내서 이를 다운로드 받아야 한다.

        messages 구조가 어떻게 생겼는지 확인하기


        '''
        # Find the message with the smallest index that has non-empty attachments
        filtered_messages = [message for message in messages if len(message.attachments) > 0]
        patched_code_attachment = filtered_messages[0].attachments[0]
        patched_code_file_id = patched_code_attachment.file_id
        print(f"patched_code_file_id: {patched_code_file_id}")

        
        patched_code_save_path = os.path.join(patched_project_save_path, get_relative_path(project_path, code_path))
        patched_code_save_path = os.path.abspath(patched_code_save_path)

        download_file(patched_code_file_id, patched_code_save_path)

        # code_patch_result {'patched_files':{원본경로:패치된파일경로, ...}, 'vulnerabilities_by_file':vulnerabilities_dict_by_file} 반환
        
        code_patch_result['patched_files'][code_path] = patched_code_save_path

    code_patch_result['vulnerabilities_by_file'] = vulnerabilities_dict_by_file

    return code_patch_result



'''
취약점이 존재하는 소스코드와 패치된 소스코드를 입력받아, 취약점과 패치 내용에 대한 설명을 반환
'''
def explain_patch(vulnerable_code_path, patched_code_path, zero_shot_cot=False):
    explain_thread = client.beta.threads.create()

    file_id_list = upload_files(get_file_list_from_path_list([vulnerable_code_path, patched_code_path]))
    attachments_list = create_attachments_list(file_id_list)

    prompt = instructions.prompt_explain_patch

    message = client.beta.threads.messages.create(
        thread_id=explain_thread.id,
        role="user",
        content=prompt,
        attachments=attachments_list,
    )    

    explain_run = client.beta.threads.runs.create(
        thread_id=explain_thread.id,
        assistant_id=get_assistant_id('explain_assistant')
    )

    start_time = time.time()

    status = check_status(explain_run.id, explain_thread.id)
    while status != 'completed':
        time.sleep(1)
        status = check_status(explain_run.id, explain_thread.id)
    
    elapsed_time = time.time() - start_time
    print("Elapsed time: {} minutes {} seconds".format(int((elapsed_time) // 60), int((elapsed_time) % 60)))
    print(f'Status: {status}')
    print('-'*50)


    messages = client.beta.threads.messages.list(
        thread_id=explain_thread.id
    )

    llm_explain_result = messages.data[0].content[0].text.value
    print(llm_explain_result)
    print('-'*50)

    
