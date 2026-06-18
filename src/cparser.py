import subprocess


def parse_file(file_path):
    with open(file_path, encoding="utf-8") as file:
        html_content = file.read()

    cpp_parser = subprocess.Popen(
        ["./parser"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    output, _ = cpp_parser.communicate(input=html_content)
    return output
