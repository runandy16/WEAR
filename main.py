import requests
import lxml.html
from tqdm import tqdm
import json
import os
import time


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def output_json(data, output_file, output_dir='', type_='w'):
    """データをTSVファイルに出力"""

    if output_dir:
        output_file = output_dir + '/' + output_file

    with open(output_file, type_,encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False, cls=SetEncoder))
        # f.write(json.dumps(data, indent=4, ensure_ascii=False))

class ScrapingWear(object):
    def __init__(self):

        self.rank_page_url = 'https://wear.jp/women-ranking/user/'
        self.usr_infos = {}
        self.dir = '/WEAR'

    def run(self):

        self.rank_page()
        output_json(self.usr_infos, 'wear_data.json', self.dir)

    def rank_page(self):

        rank_html = requests.get(self.rank_page_url).text
        rank_root = lxml.html.fromstring( rank_html)

        for usr in tqdm(range(100), desc='rank_num'):

            name = str(rank_root.cssselect('#user_ranking > ol > li:nth-child({}) > div.meta > h2'.format(usr+1))[0].text_content()).replace('/', '-')

            usr_url = 'https://wear.jp' + str(rank_root.cssselect('#user_ranking > ol > li:nth-child({}) > p.item-user-header-avatar > a'.format(usr+1))[0].get('href'))
            usr_name = str(rank_root.cssselect('#user_ranking > ol > li:nth-child({}) > p.item-user-header-avatar > a'.format(usr+1))[0].get('href')).replace('/', '')

            if not os.path.isdir(self.dir + '/'+ usr_name):
                os.mkdir(self.dir + '/' +  usr_name)
                self.usr_page(usr_url, usr_name, name)
            else:
                if not os.path.isdir(self.dir + '/' + usr_name + '/{}.json'.format(usr_name)):
                    self.usr_page(usr_url, usr_name, name)
                else:
                    continue


    def usr_page(self, target_url, usr_name, name):

        time.sleep(1)
        target_html = requests.get(target_url).text
        target_root = lxml.html.fromstring(target_html)

        usr_info = {}

        if target_root.cssselect('#user_main > section.intro > h1 > span'):
            usr_info['type'] = '公式'

        try:
            usr_info['height'] =  str(target_root.cssselect('#user_header_mini > div > div.main.clearfix > div.content > div > ul > li:nth-child(1)')[0].text_content())
            usr_info['sex'] = str(target_root.cssselect('#user_header_mini > div > div.main.clearfix > div.content > div > ul > li:nth-child(2)')[0].text_content())
            usr_info['country'] =  str(target_root.cssselect('#user_header_mini > div > div.main.clearfix > div.content > div > ul > li:nth-child(3)')[0].text_content())
            usr_info['age'] =  str(target_root.cssselect('#user_header_mini > div > div.main.clearfix > div.content > div > ul > li:nth-child(4)')[0].text_content())
            usr_info['hairstyle'] =  str(target_root.cssselect('#user_header_mini > div > div.main.clearfix > div.content > div > ul > li:nth-child(5)')[0].text_content())
        except Exception as e:
            usr_info['usr_data'] = 'None'
        pass
        usr_info['name'] = name
        usr_info['follower'] = str(target_root.cssselect('#user_menu > nav > div.sub > ul > li:nth-child(1) > a')[0].text_content())[:-5]
        usr_info['code_num'] = int(str(target_root.cssselect('#user_menu > nav > div.main > ul > li.current > a')[0].text_content())[:-7])
        usr_info['code_infos'] = []

        n, page_num = 1,1
        for code in tqdm(range(usr_info['code_num']), desc='code_num'):
            if code % 56 == 0:
                n = 1
                page_num += 1
                target_html = requests.get(target_url + '?pageno={}'.format(page_num)).text
                target_root = lxml.html.fromstring(target_html)

            code_info = {}
            try:
                code_info['plus_num'] = str(target_root.cssselect('#main_list > ul > li:nth-child({}) > div.meta.clearfix > ul > li.save.icon_font > div > p > a > span'.format(n))[0].text_content())
            except Exception as e:
                code_info['plus_num'] = ''
            try:
                code_info['like_num'] = str(target_root.cssselect('#main_list > ul > li:nth-child({}) > div.meta.clearfix > ul > li.like.icon_font > div > p > a > span'.format(n))[0].text_content())
            except Exception as e:
                code_info['like_num'] = ''

            try:
                code_url = str(target_root.cssselect('#main_list > ul > li:nth-child({}) > div.image > a'.format(n))[0].get('href'))
                usr_info = self.code_page(code_url, code_info, usr_info, usr_name, code)
            except:
                continue
            n += 1
        print(usr_info)

        output_json(usr_info, '{}.json'.format(usr_name), self.dir + '/' + usr_name)
        self.usr_infos.setdefault(usr_name ,usr_info)

    def code_page(self, code_url, code_info, usr_info, usr_name,  code):

        code_html = requests.get('https://wear.jp' + code_url).text
        code_root = lxml.html.fromstring(code_html)

        code_info['timestamp'] = str(code_root.cssselect('#coordinate_info > div > p')[0].text_content())
        code_info['browse'] = str(code_root.cssselect('#coordinate_img > p.view_num.icon_font')[0].text_content())
      
        try:
            code_info['title'] = str(code_root.cssselect('#coordinate_info > h1')[0].text_content())
        except Exception as e:
            code_info['title'] = ''
        try:
            code_info['text'] = str(code_root.cssselect('#coordinate_info > p.content_txt')[0].text_content())
        except Exception as e:
            code_info['text'] = ''

        like_num = code_info['like_num']

        src = code_root.cssselect('#coordinate_img > p.img > img')[0].get('src')
        img_name = src.replace('.jpg', '')
        img_name = img_name.replace('/', '_')
        code_info['img_name'] = f'{img_name}_{like_num}.jpg'

        if not os.path.isdir(self.dir + '/'+ usr_name + '/{}_{}.jpg'.format(img_name, code_info['like_num'])):
            with open(self.dir + '/'+ usr_name + '/{}_{}.jpg'.format(img_name, like_num), 'wb') as f:  # imgフォルダに格納
                f.write(requests.get('https:' + src).content)  # .contentにて画像データとして書き込む

        usr_info['code_infos'].append(code_info)

        return usr_info

if __name__ == '__main__':
    test = ScrapingWear()
    test.run()

