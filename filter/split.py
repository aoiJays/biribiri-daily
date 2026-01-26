def split_juya(file_path, category='AI早报'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    info_item = content.split('---')[1:-2]
    data = []

    for idx, item in enumerate(info_item):
        item = item.strip()
        data.append({
            'category': category,
            'content': item
        })
    
    return data

def split_cs(file_path, category='CS'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    info_item = '\n'.join(content.split('\n')[3:])
    data = [{
        'category': category,
        'content': info_item
    }]

    return data

def split_animation(file_path, category='动漫'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    info_item = '\n'.join(content.split('\n')[13:])
    data = [{
        'category': category,
        'content': info_item
    }]

    print(data[0]['content'])
    return data

def split_hardware(file_path, category='硬件'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    info_item = '\n'.join(content.split('\n'))
    data = [{
        'category': category,
        'content': info_item
    }]

    return data

def split_news(file_path, category='新闻'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    info_item = content.split('##')[1:]
    data = []
    for idx, item in enumerate(info_item):
        item = item.strip()
        data.append({
            'category': category,
            'content': '## '+item
        })

    return data

if __name__ == "__main__":
    data = split_news('output/md/新闻_wechat_2026-01-20 美国早报.md')
    for i in data:
        print(i['content'])
        print('---')