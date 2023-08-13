from bs4 import BeautifulSoup

# 定义一个字典用于存储英文到中文的映射关系
from translation_map import translation_map

# 读取HTML文件
with open("report.html", "r", encoding="utf-8") as file:
    html = file.read()

# 创建BeautifulSoup对象
soup = BeautifulSoup(html, "html.parser")

# 获取所有文本内容
texts = soup.findAll(text=True)

# 遍历文本内容，如果在映射字典中找到对应的英文文本，则替换为中文翻译
for i in range(len(texts)):
    text = texts[i]
    if text.strip() and not text.isnumeric():
        translation = translation_map.get(text)
        if translation:
            texts[i] = translation

# 将翻译后的文本替换回HTML中
for tag in soup():
    if tag.string:
        tag.string.replace_with(texts.pop(0))

# 保存翻译后的HTML文件
with open("report1.html", "w", encoding="utf-8") as file:
    file.write(str(soup))
print('Translation Done.')