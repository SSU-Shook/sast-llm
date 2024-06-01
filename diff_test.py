from helper_utils import *

def main():
    # 파일 1 경로
    file1_path = input("Enter the path of the first file: ")

    #파일 2 경로
    file2_path = input("Enter the path of the second file: ")

    # 파일 1 읽기
    file1 = open(file1_path, 'r')
    file1_text = file1.read()
    file1.close()

    # 파일 2 읽기
    file2 = open(file2_path, 'r')
    file2_text = file2.read()
    file2.close()

    # 파일 1과 파일 2의 차이점을 출력
    print(generate_diff(file1_text, file2_text))    


if __name__ == "__main__":
    main()