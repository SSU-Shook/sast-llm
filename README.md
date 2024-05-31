# 주요 파일 설명

## sast_llm.py
SAST의 LLM 기능과 관련된 코드입니다.  
import 하여 사용합니다.

## instructions.py
LLM 입력 프롬프트를 포함하는 파일입니다.

## patch_utils.py
코드 패치와 관련이 높은 함수들의 모음

## helper_utils.py
SAST와 직접적인 관련이 없는, 간단한 유틸리티 함수들

## vulnerability_patch_test.py
취약점 패치를 테스트 하는 스크립트입니다.  
(patch_vulnerabilities 함수 테스트)  

## code_style_profile_test.py
코드 스타일 프로파일링을 테스트 하는 스크립트입니다.  
(profile_code_style 함수 테스트)  

## explain_patch_test.py
취약점과 패치 내용에 대한 설명을 테스트합니다.  
(explain_patch 함수 테스트)

## code_style_profile_rules.md
GPT 어시스턴트에 업로드되는 코드 스타일 프로파일 포멧에 대한 설명 파일입니다.  

## comment_added_codes
LLM으로 취약점 패치 전에 취약점 정보를 주석에 추가한 코드가 저장되는 디렉터리입니다.

## patched_codes
LLM으로 취약점이 패치된 코드가 저장됩니다.



# sast_llm.py의 주요 함수

## `profile_code_style(project_path, zero_shot_cot=False)`

이 함수는 프로젝트의 코드 스타일을 분석하여 프로파일 정보를 반환합니다.

### 입력
- `project_path`: 프로젝트 경로 (문자열)
- `zero_shot_cot`: zero-shot cot를 적용할지 여부 (True|False)

### 출력
- JSON 형태의 코드 스타일 프로파일 (문자열)

---

## `patch_vulnerabilities(project_path, codeql_csv_path, code_style_profile=None, zero_shot_cot=False)`

이 함수는 프로젝트의 취약점을 패치합니다.

### 입력
- `project_path`: 프로젝트 경로 (문자열)
- `codeql_csv_path`: codeql의 결과 csv 파일 경로 (문자열)
- `code_style_profile`: 코드 스타일 프로파일 (json 문자열 혹은 None)
- `zero_shot_cot`: zero-shot cot를 적용할지 여부 (True|False)

### 출력
- 패치 결과 (딕셔너리), 다음과 같은 구조를 지닌다:
  - `'patched_file_path'`: [{원본 파일 경로: 패치된 파일 경로}, ...]
  - `'vulnerabilities_by_file'`: {원본 파일 경로: [취약점 정보1, ...]}

---

## `explain_patch(vulnerable_code_path, patched_code_path, zero_shot_cot=False)`

이 함수는 취약점과 그 패치 내용에 대해 설명합니다.

### 입력
- `vulnerable_code_path`: 취약점이 존재하는 파일의 경로 (문자열)
- `patched_code_path`: 취약점이 패치된 코드 경로 (문자열)
- `zero_shot_cot`: zero-shot cot를 적용할지 여부 (True|False)

### 출력
- 취약점과 패치 내용에 대한 설명을 반환합니다. (문자열)



# Reference

- [OPENAI FILE UPLOAD](https://platform.openai.com/docs/api-reference/files/create?lang=python)