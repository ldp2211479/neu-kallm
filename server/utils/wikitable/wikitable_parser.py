import mwxml
import wikitextparser as wtp
import bz2
from tqdm import tqdm
import argparse
import pickle
import multiprocessing as mp
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logging.info('Starting processing...')

################### table2text ###################
def TextBasedTableInput(title, columns, rows):
    """
    Serialise a table into a sentence
    "separation_tokens": {"header_start": "<HEADER>", "header_sep": "<HEADER_SEP>", "header_end": "<HEADER_END>", "row_start": "<ROW>", "row_sep": "<ROW_SEP>", "row_end": "<ROW_END>"}
    """
    table_sentences = []

    table_sentences.append("<BOT>")
    # add table titles
    table_sentences.append(title)
    table_sentences.append("<EOT>")
    
    table_sentences.append("<HEADER>")
    for column_name in columns:
        if column_name:
            table_sentences += [column_name, "<HEADER_SEP>"]
        else:
            table_sentences += [" ", "<HEADER_SEP>"]
    table_sentences.append("<HEADER_END>")

    for row in rows:
        table_sentences.append("<ROW>")
        for cell in row:
            if cell:
                table_sentences += [cell, "<ROW_SEP>"]
            else:
                table_sentences += [" ", "<ROW_SEP>"]
        table_sentences.append("<ROW_END>")

    table_sentence = " ".join(table_sentences).strip()
    return table_sentence

################### infobox2table ###################
def find_infobox(text):
    stack = []
    i = 0
    while i < len(text):
        if text[i:i+2] == '{{':
            stack.append(i)
            i += 2
        elif text[i:i+2] == '}}' and stack:
            start = stack.pop()
            if not stack:
                block_text = text[start:i]
                if "infobox" in block_text.lower() or "taxobox" in block_text.lower():
                    # del the head of infobox, only get the key and value( | key = value )
                    block_text = re.sub(r'^.*?\|', '|', block_text, count=1, flags=re.DOTALL)
                    return [(block_text, text[start:i+2])] + find_infobox(block_text)   # find the sub infobox of the main infobox
            i += 2
        else:
            i += 1
    return []

def parser_infobox2table(block_text):
    # del image
    pattern = re.compile(r'\{\{.*?image[\s\S]*?\}\}', re.IGNORECASE)
    block_text = re.sub(pattern, ' ', block_text, re.DOTALL)
    # del list
    pattern = re.compile(r'\{\{collapsible[\s\S].*?list[\s\S]*?\}\}', re.IGNORECASE)
    block_text = re.sub(pattern, ' ', block_text, re.DOTALL)
    # del non-value
    block_text = re.sub(r'\|\s*\w+\s*=\s*(?=\n\s*\|)', '', block_text)
    # table
    pattern = r'\|\s*([^\|=\n]+?)\s*=\s*(.*?)(?=\n\s*\|\s*[^\|=]+?\s*=\s*|$)'
    matches = re.findall(pattern, block_text, re.DOTALL)
    table = [[i[0] for i in matches], [i[1] for i in matches]]
    return table

################### wikilist2text ###################
def list2text(rows):
    other_list_fir = ['bulleted list', 'unbulleted list', 'horizontal list', 'ordered list', 'horizontal_ordered list', '{{hlist', '{{ubl', '{{ubt', '{{ublist', '{{unbullet']
    other_list_sec = ['#invoke:list|bulleted', '#invoke:list|unbulleted', '#invoke:list|horizontal', '#invoke:list|ordered', '#invoke:list|horizontal_ordered']
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if not cell:
                continue
            # flatlist
            if 'flatlist' in cell:
                match = re.search(r'\{\{flatlist\|\s*\n(.*?)\n\s*\}\}', cell, re.DOTALL)
                if match:
                    cell = match.group(1).strip()     
            parsed = wtp.parse(cell)
            # list
            l = parsed.get_lists()
            if l:
                l = l[0].items
                try:
                    content_without_list = re.search(r"(.*?)\*", cell, re.DOTALL).group(1).replace("\n", ",")
                    rows[i][j] = content_without_list + ', '.join(item.strip() for item in l)
                except:
                    rows[i][j] = ', '.join(item.strip() for item in l)
            # other list
            if any(list_name in cell.lower() for list_name in other_list_fir):
                l = re.sub(r'\|[\w]+_style[^|]*', '', cell)
                l = re.split(r'\|(?![^{]*\}\})', l[2:-2])[1:]
                rows[i][j] = ', '.join(item.strip() for item in l)
            if any(list_name in cell.lower() for list_name in other_list_sec):
                l = re.sub(r'\|[\w]+_style[^|]*', '', cell)
                l = re.split(r'\|(?![^{]*\}\})', l[2:-2])[2:]
                rows[i][j] = ', '.join(item.strip() for item in l)             
    return rows

def clear_br_for_table(columns, rows):
    index = []
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if '\n' in cell:
                index.append(j)
    for i in sorted(index, reverse=True):
        del columns[i]
        for j, row in enumerate(rows):
            del rows[j][i]
    return columns, rows

################### page ###################
# 更改xml注释
def clean_xml_comment(text):
    return re.sub(r"<!--.*?-->", "", text, re.DOTALL)

def serialize_page(page):
    return {'title': page.title, 'revisions': [rev.text for rev in page]}

def deserialize_page(serialized_page):
    class Page:
        def __init__(self, title, revisions):
            self.title = title
            self.revisions = revisions
    
    return Page(serialized_page['title'], serialized_page['revisions'])

def process_page(serialized_page):
    page = deserialize_page(serialized_page)
    tables_text = []
    for wiki_text in page.revisions:
        if isinstance(wiki_text, str):
            wiki_text = clean_xml_comment(wiki_text)
            # table
            parsed = wtp.parse(wiki_text)
            for table in parsed.tables:
                t = table.data()
                if not t:
                    continue
                columns = t[0]
                rows = list2text(t[1:])
                if not any(rows):
                    continue
                tables_text.append(TextBasedTableInput(page.title, columns, rows))
                if len(tables_text) >= 100:  
                    yield tables_text
                    tables_text = []
            # infobox
            infoboxes = find_infobox(wiki_text)
            infoboxes, infoboxes_with_braces = [i[0] for i in infoboxes], [i[1] for i in infoboxes]
            if infoboxes:
                if len(infoboxes)>1:
                    for i in range(1, len(infoboxes)):
                        infoboxes[0] = infoboxes[0].replace(infoboxes_with_braces[i], "")
                for infobox in infoboxes:
                    t = parser_infobox2table(infobox)
                    if not t:
                        continue  
                    columns = t[0]
                    rows = list2text(t[1:])
                    columns, rows = clear_br_for_table(columns, rows)
                    if not any(rows):
                        continue
                    tables_text.append(TextBasedTableInput(page.title, columns, rows))
                    if len(tables_text) >= 100:  
                        yield tables_text
                        tables_text = []
        else:
            logging.error(page.title)
    if tables_text:
        yield tables_text

def process_and_store_page(page_and_list):
    page = page_and_list[0]
    result_list, counter, stop_event, lock = page_and_list[1]
    # if stop_event.is_set():
    #     return
    for tables_text in process_page(page):
        if tables_text:
            result_list.append(tables_text)
    # with lock:
    #     counter.value += 1
    #     if counter.value >= 1000:  # 设置处理数量限制
    #         stop_event.set()

def get_tables_text(args):
    with bz2.open(args.path_dump_file, 'rb') as file:
        dump = mwxml.Dump.from_file(file)

        def page_generator(dump):
            for page in dump:
                yield serialize_page(page)
       
        manager = mp.Manager()
        result_list = manager.list()

        counter = manager.Value('i', 0)
        stop_event = manager.Event()
        lock = manager.Lock()

        with mp.Pool(mp.cpu_count()) as pool:
            for _ in tqdm(pool.imap_unordered(process_and_store_page, ((page, (result_list, counter, stop_event, lock)) for page in page_generator(dump))), desc="Processing pages"):
                if stop_event.is_set():
                    break
                pass
        
        # Combine results and write to file
        combined_tables_text = [table for sublist in result_list for table in sublist]
        with open(args.path_tables_text, "wb") as f:
            pickle.dump(combined_tables_text, f)


def main():
    arg_parser = argparse.ArgumentParser(description="")
    arg_parser.add_argument('--path_dump_file', default="./dataset/enwiki-latest-pages-articles.xml.bz2", type=str, help='The path to wikipedia dump')
    arg_parser.add_argument('--path_tables_text', default="./dataset/wikitable/tables_text.pkl", type=str, help='The path to wikitables text')
    
    args = arg_parser.parse_args()

    get_tables_text(args)
    

if __name__ == "__main__":
    main()
