'''
취약점 패치와 상대적으로 관련이 높은
유틸리티 함수 모음
'''


from helper_utils import *


def forge_vulnerability_comment(vulnerability):
    '''
    취약점 정보를 입력받아 취약점에 대한 주석을 생성한다.
    '''
    comment = '/*'
    comment += f'Vulnerability name: {vulnerability["name"]}'
    comment += f'\tVulnerability description: {vulnerability["description"]}'
    comment += f'\tVulnerability message: {vulnerability["message"]}'
    comment += '*/'

    return comment


def comment_source_code(file_path, vulnerabilities):
    '''
    코드 파일의 경로를 입력받아서 취약점 정보를 주석으로 추가한다.
    '''
    lines = []
    with open(file_path, 'r', encoding='UTF8') as file:
        lines = file.readlines()

    for vulnerability in vulnerabilities:
        comment = forge_vulnerability_comment(vulnerability)
        lines[vulnerability['start_line'] - 1] = lines[vulnerability['start_line'] - 1][:-1] + (' ' + comment) + '\n'

    with open(file_path, 'w', encoding='UTF8') as file:
        file.writelines(lines)


def extract_code(text): 
    '''
    LLM의 출력을 입력받아 소스코드를 추출하여 반환한다.
    반환 형태: [(언어, 코드), ...]
    '''
    try:
        if '```' in text:
            matches = re.findall(r'`{3}(.*?)\n(.*?)`{3}', text, re.DOTALL)
            return matches

        else:
            return [text,]
        
    except Exception as exception:
        return [text,]


def diff_code(code1, code2):
    '''
    두 코드를 비교하여 diff를 반환
    '''
    code1 = code1.splitlines()
    code2 = code2.splitlines()
    diff = difflib.unified_diff(code1, code2, lineterm='')
    return '\n'.join(diff)


def preprocess_code(file_path):
    '''
    파일에서 쉬뱅을 삭제한다.
    '''
    with open(file_path, 'r', encoding='UTF8') as file:
        lines = file.readlines()
    
    if lines and lines[0].startswith('#!'):
        lines[0] = '\n'

    temp_dir = tempfile.mkdtemp()
    filename = get_file_name_from_path(file_path)
    temp_file_path = os.path.join(temp_dir, filename)

    with open(temp_file_path, 'w', encoding='UTF8') as file:
        file.writelines(lines)
    
    return temp_file_path



def parse_codeql_csv(csv_file_path):
    '''
    Parses the output CSV file from CodeQL and returns a dictionary.
    '''

    f = open(csv_file_path, 'r', encoding='utf-8')
    rdr = csv.reader(f)

    vulnerabilities_list = list()
    for line in rdr:
        vulnerabilities_list.append(line)
    f.close()

    vulnerabilities_dict_list = list()
    for vulnerability in vulnerabilities_list:
        vulnerability_dict = dict()
        vulnerability_dict['name'] = vulnerability[0]
        vulnerability_dict['description'] = vulnerability[1]
        vulnerability_dict['severity'] = vulnerability[2]
        vulnerability_dict['message'] = vulnerability[3]
        vulnerability_dict['path'] = vulnerability[4]
        vulnerability_dict['start_line'] = int(vulnerability[5])
        vulnerability_dict['start_column'] = int(vulnerability[6])
        vulnerability_dict['end_line'] = int(vulnerability[7])
        vulnerability_dict['end_column'] = int(vulnerability[8])

        #print(vulnerability_dict)
        vulnerabilities_dict_list.append(vulnerability_dict)

    return vulnerabilities_dict_list

