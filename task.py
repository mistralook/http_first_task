import socket
import re
import sys


def parse(content):
    patterns = {
        "В запросе должны быть выставлены cookie": "Cookie",
        "Запрос должен иметь следующие данные фо": "Forms",
        "Запрос должен иметь следующие заголовки": "Headers",
        "При переходе выставьте следующие параме": "Params",
        "Загрузите файлы по адресу": "Files"}

    task_type, address = get_task_type(content)
    pairs = get_pairs(content, patterns)
    query = create_http_data(task_type, address, pairs)
    return query


def get_task_type(content):
    task_type = None
    address = None

    if "Секретный ключ" in content[-3]:
        print(re.findall("<code>(.*)</code>",
                         content[-3])[0])
        sys.exit(0)

    if "POST" in content[12]:
        task_type = "POST"
        address = re.findall("<code>(.*)</code>",
                             content[12])[0]

    if "Загрузите " in content[12]:
        task_type = "POST"
        address = re.findall("<code>(.*)</code>",
                             content[12])[0]

    if "GET" in content[12]:
        task_type = "GET"
        address = re.findall("<code>(.*)</code>",
                             content[12])[0]

    if "Перейдите по" in content[12]:
        task_type = "GET"
        mo = re.findall('<a href="(.*)">',
                        content[12])
        if not mo:
            mo = re.findall("<a href='(.*)'>",
                            content[12])
        address = mo[0]

    return task_type, address


def get_pairs(content, patterns):
    pairs = dict()
    size = 39
    current_pattern = None
    for line in content:
        pattern = line[:size]
        if pattern in patterns:
            current_pattern = pattern
            config = patterns[current_pattern]
            if config not in pairs:
                pairs[config] = list()
        elif "Загрузите" in pattern:
            current_pattern = "Загрузите файлы по адресу"
            config = patterns[current_pattern]
            if config not in pairs:
                pairs[config] = list()
        else:
            mo = re.findall("<code>(.*)</code>", line)
            if mo:
                if current_pattern is not None:
                    config = patterns[current_pattern]
                    pairs[config].append(mo[0])
    return pairs


def create_http_data(*args):
    task_type = args[0]
    address = args[1]
    pairs = args[2]
    params = [address]
    forms = list()
    cookie = ["Cookie: user=b17eb120337154346abac913ee06b27c"]
    files = list()
    headers = list()
    for config in pairs:
        if config == "Cookie":
            for i in range(1, len(pairs[config]), 2):
                line = f"; {pairs[config][i - 1]}={pairs[config][i]}"
                cookie.append(line)

        if config == "Headers":
            for i in range(1, len(pairs[config]), 2):
                key = pairs[config][i - 1]
                value = pairs[config][i]
                line = f"{key}: {value}"
                headers.append(f'{line}\r\n')

        if config == "Params":
            params.append("?")
            for i in range(1, len(pairs[config]), 2):
                line = f"{pairs[config][i - 1]}={pairs[config][i]}&"
                if i == len(pairs[config]) - 1:
                    line = line[:-1]
                params.append(line)

        if config == "Forms":
            for i in range(1, len(pairs[config]), 2):
                key = pairs[config][i - 1]
                value = pairs[config][i]
                line = f"{key}={value}&"
                if i == len(pairs[config]) - 1:
                    line = line[:-1]
                forms.append(line)

        if config == "Files":
            for i in range(1, len(pairs[config]), 2):
                line = f"{pairs[config][i - 1]}={pairs[config][i]}"
                files.append(line)

    return f"{task_type}: {''.join(params)}", cookie, headers, forms, files


def create_bytes_message(data):
    address = data[0].split(": ")[1]
    request_type = data[0].split(": ")[0]
    cookie = data[1]
    headers = data[2]
    forms = data[3]
    files = data[4]
    result = f"{request_type} {address} HTTP/1.0\r\nHost: hw1.alexbers.com\r\n{''.join(cookie)}\r\n"

    if headers:
        result += f"{''.join(headers)}"

    if forms:
        str_forms = ''.join(forms)
        content_len = len(str_forms.encode('utf-8'))
        result += f"Content-Type: application/x-www-form-urlencoded\r\nContent-Length: {content_len}\r\n\r\n{str_forms}\r\n\r\n"

    if files:
        entity_body = '\r\n'
        for f in files:
            name = f.split("=")[0]
            value = f.split("=")[1]
            entity_body += f'\r\n--boundary\r\nContent-Disposition: form-data; name="{name}"; filename="{name}"\r\n\r\n{value}'
        entity_body += "\r\n--boundary--\r\n"
        entity_body_len = len(entity_body.encode('utf-8')) - 6
        result += f'Content-Type: multipart/form-data; boundary=boundary\r\n'
        result += f'Content-Length: {entity_body_len}{entity_body}'

    if not headers and not forms and not files:
        result += "\r\n"

    if headers and not forms and not files:
        result += "\r\n"
    result = result.encode("utf-8")

    return result
dd

def main():
    current_message = b"GET / HTTP/1.0\r\nHost: hw1.alexbers.com\r\nCookie: user=b17eb120337154346abac913ee06b27c\r\n\r\n"
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("hw1.alexbers.com", 80))
        sock.sendall(current_message)
        data = b""
        while True:
            current_data = sock.recv(8000)
            if len(current_data) == 0:
                break
            data += current_data
        sock.close()
        content = data.decode("utf-8").split("\n")
        parsed_data = parse(content)
        current_message = create_bytes_message(parsed_data)


if __name__ == "__main__":
    main()
