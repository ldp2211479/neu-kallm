import re
from tqdm import trange, tqdm
import pickle
import multiprocessing as mp


############# stand long sentence #############
def clean_long_sentence(text):
    clean_text = text
    clean_text = re.sub(r'\{\{col-begin.*?\}\}.*?\{\{col-end.*?\}\}', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'\{\|class=.*?\|\}', '', clean_text, flags=re.DOTALL)

    return clean_text


############# stand table #############
# 更改无序表格
def clean_list(text):
    clean_text = text
    def process_sep_content(match):
        content = match.group(0)
        sentences = re.split(r'\*+', content)
        sentences = [s.strip().strip('.') for s in sentences if s.strip()]
        new_content = ', '.join(sentences)
        return f'<ROW_SEP> {new_content} <ROW_SEP>'
    def process_row_content(match):
        content = match.group(1)
        sentences = re.split(r'\*+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        new_content = ', '.join(sentences)
        return f'<ROW> {new_content} <ROW_SEP>'
    clean_text = re.sub(r'(?<=<ROW_SEP>).*?(?=<ROW_SEP>)', process_sep_content, clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'<ROW>(.*?)<ROW_SEP>', process_row_content, clean_text, flags=re.DOTALL)
    return clean_text
# 更改单位转换
def clean_convert(text):
    clean_text = text
    clean_text = re.sub(r"\{\{convert\|([^|]+)\|(-|to|and)\|([^|]+)\|([^|]+)\|.*?\}\}", r'\1 \2 \3 \4', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r"\{\{convert\|([^|]+)\|([^|]+)\|.*?\}\}", r'\1 \2', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r"\{\{cvt\|([^|]+)\|([^|]+)\|.*?\}\}", r'\1 \2', clean_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_text
# 更改一些不常见的模板
def clean_others(text):
    clean_text = text
    clean_text = clean_text.replace(r'\{\{Snd\}\}', "-")
    clean_text = re.sub(r"\{\{Sort\|([^|]+)\|([^|]+)\}\}", r'\2', clean_text, flags=re.IGNORECASE | re.DOTALL)                                                           
    clean_text = re.sub(r'\{\{[^{}]*efn[^{}]*\}\}', '', clean_text, flags=re.IGNORECASE | re.DOTALL)                         
    clean_text = re.sub(r'\{\{clarify.*\}\}', '', clean_text, flags=re.IGNORECASE | re.DOTALL)                     
    clean_text = re.sub(r'\{\{chset-table-footer*?\}\}', '', clean_text, flags=re.IGNORECASE | re.DOTALL)          
    clean_text  = re.sub(r"\{\{chset-ctrl1[^|]+\|[^|]+\|([^|]+)\}\}", r'\1', clean_text)        
    clean_text  = re.sub(r"\{\{chset-ctrl1[^|]+\|[^|]+\|([^|]+)\|[^|]+\}\}", r'\1', clean_text)  
    clean_text = re.sub(r'\{\{chset-table-footer.*\}\}', ' ', clean_text, flags=re.IGNORECASE | re.DOTALL)          
    clean_text = re.sub(r'<syntaxhighlight.*?>.*?</syntaxhighlight>', '', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r'<span.*?>.*?</span>', '', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r'<!--.*?-->', '', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r'\{\|.*?\|\}', '', clean_text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r'\{\{(abbr|Abbrlink)\|([^|]+)\|[^}]+\}\}', r'\1', clean_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_text
# 更改回车
def clean_br(text):
    clean_text =  text.replace("<br>", " ")
    clean_text = clean_text.replace("<br />", " ")
    clean_text = clean_text.replace("<br/>", " ")
    return clean_text
# 更改图标
def clean_flag(text):
    clean_text = re.sub(r'\{\{flag\|([^|]+)\}\}', r'\1', text)
    clean_text = re.sub(r'\{\{Flag\|([^|]+)\}\}', r'\1', clean_text)
    clean_text = re.sub(r'\{\{flagu\|([^|]+)\}\}', r'\1', clean_text)
    clean_text = re.sub(r'\{\{Flagu\|([^|]+)\}\}', r'\1', clean_text)
    clean_text = re.sub(r'\{\{flagicon\|([^|]+)\}\}', r'\1', clean_text)
    return clean_text
# 更改字体和大小
def clean_font(text):
    clean_text = re.sub(r"\{\{font color\|[^|]+\|([^|]+)\}\}", r'\1', text)
    clean_text = re.sub(r'\{\{small\|([^|]+)\}\}', r'\1', clean_text)
    clean_text = re.sub(r'\{\{Small\|([^|]+)\}\}', r'\1', clean_text)
    return clean_text
# 更改提示词
def clean_tooltip(text):
    return re.sub(r"\{\{Tooltip\|([^|]+)\|([^|]+)\}\}", r'\1(\2)', text)
# 更改引用超链接
def clean_ref(text):
    clean_text = re.sub(r'<ref.*?/>', '', text, flags=re.DOTALL)
    clean_text = re.sub(r'<ref.*?>.*?</ref>', '', clean_text, flags=re.DOTALL)
    return clean_text
# 更改文字超链接
def clean_word_ref(text):
    clean_text = re.sub(r'\[\[[^\[\]]+\|([^\[\]]+)\]\]', r'\1', text)
    clean_text = re.sub(r'\[\[([^\[\]]+)\]\]', r'\1', clean_text)
    return clean_text

# 更改作者信息
def clean_harvnb(text):
    clean_text = re.sub(r'\{\{harvnb\|([^|]+)\|([^|]*?)\}\}', r'\1, \2', text)
    clean_text = re.sub(r'\{\{harvnb\|([^|]+)\|([^|]*?)\|([^|}]+)\}\}', r'\1, \2, \3', clean_text)
    clean_text = re.sub(r'\{\{harvnb\|([^|]+)\|([^|]*?)\|([^|]*?)\|([^|}]+)\}\}', r'\1, \2, \3, \4', clean_text)
    return clean_text
# 更改notelist结构
def clean_notelist(text):
    notelist_pos = text.find('{{notelist')
    text = re.sub(r'\{\{efn.*?\}\}', '', text, flags=re.DOTALL)
    if notelist_pos != -1:
        cleaned_text = text[:notelist_pos]
        cleaned_text = re.sub(r'<ROW>(?!.*<ROW>).*\Z', '', cleaned_text, flags=re.DOTALL)
        return cleaned_text
    else:
        return
 # 更改树结构
def clean_tree(text):
    # 提取<BOT>到<HEADER_END>之间的内容，保留不变
    header_match = re.search(r'(<BOT>.*?<HEADER_END>)', text, re.DOTALL)
    header_content = header_match.group(1) if header_match else ""
    # 提取{{tree list}}到{{tree list/end}}之间的内容，并将树结构转换为列表形式
    tree_lists = re.findall(r'{{tree list}}(.*?){{tree list/end}}', text, re.DOTALL)
    new_rows = []
    for tree in tree_lists:
        # 删除*号前缀和多余的引号
        tree = re.sub(r'\*\*?\s*\'*', '', tree)
        tree = re.sub(r'\'*\s*\{\{efn.*?\}\}', '', tree)
        tree = re.sub(r'\'*\s*\[\[.*?\]\]', '', tree)
        # 删除多余的标点和空白符
        tree = re.sub(r'[\'\*\[\]]', '', tree)
        tree = tree.strip()
        # 将各行内容合并为逗号隔开的列表
        tree_list = tree.split('\n')
        tree_list = [item.strip() for item in tree_list if item.strip()]
        new_row = ', '.join(tree_list)
        new_rows.append(new_row)
    # 生成新的<ROW>内容
    new_row_content = ' <ROW> ' + ' <ROW_SEP> '.join(new_rows) + ' <ROW_SEP> <ROW_END>'
    # 将header内容和新的<ROW>内容组合
    clean_text = header_content + new_row_content
    return clean_text
# 更改div块
def clean_div(text):
    clean_text = re.sub(r'<div.*?>(.*?)</div>', r'\1', text, flags=re.DOTALL)
    clean_text = re.sub(r'\s+', ' ', clean_text)  
    return clean_text


