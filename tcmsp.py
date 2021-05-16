import requests
from bs4 import BeautifulSoup
import re
import xlsxwriter
import pandas as pd

#  给出一个中药列表（需要在tcmsp中找到，返回化合物-靶点对数据，也可以只返回靶点）

def get_all_target():
    path = '1.txt'
    with open(path, 'r') as f:
        cont = f.read()
    # 两次使用正则获取靶向基因
    TAR_ID = re.findall(r'TAR_ID":"(.*?)"', cont)
    drugbank_ID = re.findall(r'drugbank_ID":"(.*?)"', cont)
    target_name = re.findall(r'target_name":"(.*?)"', cont)
    print('searching---', len(TAR_ID), len(drugbank_ID), len(target_name))
    TAR_ID_list = []
    drugbank_ID_list = []
    target_name_list = []

    for t in TAR_ID:
        TAR_ID_list.append(t)
    for t in drugbank_ID:
        drugbank_ID_list.append(t)
    for t in target_name:
        target_name_list.append(t)

    df = pd.DataFrame({'TAR_ID_list': TAR_ID_list,
                     'drugbank_ID_list': drugbank_ID_list,
                     'target_name_list': target_name_list})
    print(df)

    return TAR_ID_list, drugbank_ID_list, target_name_list


class get_drug_target(object):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        }
        self.base_url = 'https://tcmspw.com/tcmspsearch.php?'

    def get_url(self, drug):

        url = self.base_url+'qs=herb_all_name&q='+drug+'&token=823a9cd270c3af0d2f9ea5dfa3626133'

        response = requests.get(url, verify=False)
        data = response.content.decode()

        return data


    def search_drug_url(self, data):
        soup = BeautifulSoup(data, 'lxml')
        drug_url1 = soup.find_all('script')
        drug_url1 = str(drug_url1)

        # 获取英文名
        drug_name1 = re.search(r'"herb_en_name":"(.*?)"', drug_url1).group(1)
        # 将英文名之间的空格替换为 %20
        drug_name2 = drug_name1.replace(' ', '%20')
        # 获取url地址
        drug_url2 = re.search(r"href='(.+)'", drug_url1).group(1)
        # print(drug_url2)
        # 拼接url
        combined_url = 'https://tcmspw.com/'+drug_url2.split('$')[0]+drug_name2+drug_url2.split('}')[1]
        return combined_url

    def get_target(self, url):
        response = requests.get(url, verify=False)  # headers=self.headers

        soup = BeautifulSoup(response.content, 'lxml')
        # 一共10个script
        total = soup.find_all('script')
        total = str(total)
        # print(total)

        # 两次使用正则获取靶向基因
        all_info = re.search(r'JSON.parse(.+)', total).group(1)
        single_target = re.findall(r'label\\":\\"(.*?)\\"', all_info)
        target_info = re.findall(r'source\\":\\"(.*?)\\"', all_info)
        drug_info = re.findall(r'target\\":\\"(.*?)\\"', all_info)

        all_info2 = re.search(r'#grid2(.+)#grid3', total, re.S).group(1)  # data:(.+)

        MOL_ID = re.findall(r'"MOL_ID":"(.*?)"', all_info2)
        # print(len(MOL_ID))

        print('---', len(target_info), len(MOL_ID), len(drug_info))
        target_list = []
        drug_list = []
        MOL_list = []
        for t in target_info:
            target_list.append(t.replace('\\\\', ''))
        for t in drug_info:
            drug_list.append(t.replace('\\\\', ''))
        for m in MOL_ID:
            MOL_list.append(m)

        return drug_list, target_list, MOL_list, single_target

    def run(self):
        drug_list = ['黄芪', '当归', '白芍', '甘草', '党参', '桂枝']  # TODO
        with xlsxwriter.Workbook('小方子.xlsx') as writer:
            sheet = writer.add_worksheet('TCM_target')
            for index, drug in enumerate(drug_list):
                col1 = 3 * index
                col2 = 3 * index + 1
                col3 = 3 * index + 2
                # print(col1, col2)
                data = self.get_url(drug)
                combined_url = self.search_drug_url(data)
                drug_data, target_data, mol_data, single_target = self.get_target(combined_url)
                Pair = True  # 如果要保存的是一对数据
                if Pair:
                    sheet.write(0, col1, drug_list[index] + 'Drug')
                    sheet.write(0, col2, drug_list[index] + 'Target')
                    sheet.write(0, col3, drug_list[index] + 'Mol_ID')
                    sheet.write_column(1, col1, drug_data)
                    sheet.write_column(1, col2, target_data)
                    sheet.write_column(1, col3, mol_data)
                else:
                    sheet.write(0, index, drug_list[index] + 'single_target')
                    sheet.write_column(1, index, single_target)

        writer.close()

if __name__ == '__main__':
    buger = get_drug_target()
    buger.run()

