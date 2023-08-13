import re
from translation_map import translation_map


def read_text_from_file(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text


def extract_translatable_text(text):
    pattern = r'>(.*?)<'
    matches = re.findall(pattern, text)
    return matches


def translate_text(text, translation_map):
    if text in translation_map:
        return translation_map[text]
    else:
        return text


def replace_translated_text(text, translated_text):
    pattern = r'>(.*?)<'
    replaced_text = re.sub(rf'{re.escape(pattern)}', translated_text, text)
    return replaced_text


def write_text_to_file(text, file_path):
    with open(file_path, 'w') as file:
        file.write(text)


# 自定义的翻译映射
# translation_map = {
#     'test': '测试',
#     'example': '示例',
# }

# 从 report.txt 文件中读取内容
print('# 从 report.txt 文件中读取内容')
input_file_path = 'report.txt'
text = read_text_from_file(input_file_path)

# 提取需要翻译的文本
print('# 提取需要翻译的文本')
translatable_text = extract_translatable_text(text)

# 对文本进行翻译
print('# 对文本进行翻译')
translated_text = []
for text in translatable_text:
    translated = translate_text(text, translation_map)
    translated_text.append(translated)

# 将翻译后的文本替换回原始文本中
print('# 将翻译后的文本替换回原始文本中')
output_text = text
for i, text in enumerate(translatable_text):
    output_text = replace_translated_text(output_text, translated_text[i])

# 将翻译结果写入 report1.html 文件中
print('# 将翻译结果写入 report1.html 文件中')
output_file_path = 'report1.html'
write_text_to_file(output_text, output_file_path)
