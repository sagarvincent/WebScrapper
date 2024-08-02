import subprocess

def file_to_parse():
    with open('file_path') as file:
        html_content = file.read()
    # create a sub process
    cpp_parser = subprocess.Popen(['./parser'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    output,error = cpp_parser.communicate(input=html_content)

    return output