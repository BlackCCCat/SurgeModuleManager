# -*- coding: utf-8 -*-
# version:20250504

__version__ = "20250504"


import os
import requests
import re
import json
from threading import Thread
from typing import List, Dict

import warnings
from urllib3.exceptions import InsecureRequestWarning


# 禁用警告
warnings.filterwarnings("ignore", category=InsecureRequestWarning)
# 在使用 requests 库进行 HTTPS 请求之前禁用警告
requests.packages.urllib3.disable_warnings()

import urllib3
urllib3.disable_warnings()

class Process(object):
    
    def __init__(self,module_info_dir,module_dir):
        self.module_info_dir = os.path.join(module_info_dir, 'modules.json')
        self.module_dir = module_dir
        self.check()
        
    def check(self) -> None:
        """
        检查模块信息文件和模块存储路径是否存在，不存在则创建
        """
        if not os.path.isfile(self.module_info_dir):
            with open(self.module_info_dir, 'wb') as f:
                f.write(''.encode())
        
        if not os.path.isdir(self.module_dir):
            os.makedirs(self.module_dir)


    def readJsonFile(self) -> List[Dict[str, str]]:
        """
        读取modules.json
        """
        with open(self.module_info_dir, 'rb') as f:
            content = f.read().decode()
        
        try:
            modules = json.loads(content)
        except:
            print('当前无模块信息')
            modules = []
        return modules
        
    def saveJsonFile(self, modules_info: List[Dict[str, str]]) -> None:
        """
        保存到modules.json
        """
        modules_info_str = json.dumps(modules_info, ensure_ascii=False, indent=4)
        modules_info_byte = modules_info_str.encode()
        with open(self.module_info_dir, 'wb') as f:
            f.write(modules_info_byte)
            # json.dump(modules_info, f, ensure_ascii=False)
    
    def exists_links(self,new_url,new_name,modules_info):
        """
        判断链接及定义的文件名称是否已存在
        """
        url_check, name_check = 0, 0

        exists_links, exists_names = [], []
        for module in modules_info:
            exists_links.append(module["link"])
            exists_names.append(module["name"])
        
            
        if new_url in exists_links:
            url_check = 1
        if new_name in exists_names:
            name_check = 1
        
        return url_check, name_check

    # 添加模块及下载链接
    def add_links(self):
        """
        添加模块及下载链接等信息
        """
        modules_info = self.readJsonFile()
        count = 0
        loop = True
        while loop:
            input_module_info = input('请输入模块名称和下载链接(以@分割:name@links[@sysinfo])')
            if input_module_info and '@' not in input_module_info:
                print('格式输入错误')
                continue

            if input_module_info:
                try:
                    add_module_name = input_module_info.split('@')[0]
                    add_module_link = input_module_info.split('@')[1]
                    add_module_sysinfo = input_module_info.split('@')[2]
                except:
                    add_module_name = input_module_info.split('@')[0]
                    add_module_link = input_module_info.split('@')[1]
                    add_module_sysinfo = ''

                url_exists, name_exists = self.exists_links(add_module_name,add_module_link,modules_info)
                if not url_exists:
                    if not name_exists:
                        add_category = self.selectCategory()
                        modules_info.append({'name': add_module_name, 'link':add_module_link, 'system':add_module_sysinfo, 'category':add_category})
                        self.download_module(add_module_name,add_module_link,add_module_sysinfo,add_category)
                        self.saveJsonFile(modules_info)
                        count += 1
                    else:
                        print('当前系统下名称重复')
                else:
                    print('链接已存在')
            else:
                loop = False

        print(f'共添加并下载{count}个模块')

    # 下载
    def download_module(self,module_name,module_link,system_info,module_category):
        """
        下载
        :param module_name: 模块名称
        :param module_link: 模块下载链接
        :param system_info: 系统信息
        :param module_category: 模块分类
        """
        res = requests.get(module_link,verify=False)
        if res.status_code == 200 and ('text/plain' in res.headers.get('Content-Type') or 'application/octet-stream' in res.headers.get('Content-Type')):
            if '🔗' not in res.text:
                # modify the content
                new_content = re.sub(r'#!\s*name\s*=', '#!name=🔗', res.text)
                
            if system_info:
                if re.search('(?i)ios',system_info):
                    sysinfo = '#!system=ios\n'
                elif re.match('(?i)mac',system_info):
                    sysinfo = '#!system=mac\n'
            else:
                sysinfo = ''
            
            if '#!system' not in new_content:
                res_content = sysinfo + new_content
            else:
                res_content = new_content
            
            if module_category:
                if '#!category' in res_content:
                    all_content = re.sub(r'(#!\s*category\s*=).*', f'#!category={module_category}\n', res_content)
                else:
                    all_content = f'#!category={module_category}\n' + res_content
            else:
                all_content = res_content
                

            # 写入指定路径并以module_name命名
            file_name = module_name + '.sgmodule'
            whole_file_name = os.path.join(self.module_dir,file_name)
            with open(whole_file_name,'wb') as mf:
                mf.write(all_content.encode())

            print(f'✅ {module_name}(链接为:{module_link}) 已下载')
            return True
        elif res.status_code == 404:
            print(f'🈳 {module_name}(链接为:{module_link}) 不存在,请检查GitHub地址是否正确')
        else:
            print(f'❌ Download {module_name} failed')
            return False

    # 修改文件名
    def modifyFilename(self, old_name, new_name):
        """
        修改文件名
        """
        modules_list = os.listdir(self.module_dir)
        old_module_name, new_module_name = old_name + '.sgmodule', new_name + '.sgmodule'
        if old_module_name in modules_list:
            os.rename(os.path.join(self.module_dir, old_module_name), os.path.join(self.module_dir, new_module_name))
            print(f'✅ 修改文件名 {old_name} 成功')
        else:
            pass

    # 删除模块文件
    def delete_module(self, module_name) -> bool:
        """
        删除模块文件
        """
        file_name = module_name + '.sgmodule'
        remove_module_dir = os.path.join(self.module_dir, file_name)
        if os.path.exists(remove_module_dir):
            os.remove(remove_module_dir)
            return True


    def selectCategory(self, type='add'):
        """
        获取分类信息，并选择一个分类，返回该分类名称
        """
        categories = []
        modules_info = self.readJsonFile()

        for item in modules_info:
            category_info = item.get("category")
            if category_info:
                categories.append(category_info)

        unique_categories = list(set(categories))

        for idx, k in enumerate(unique_categories):
            print(f'{idx+1}. {k}')

        if type == 'add':
            category = input('请输入分类序号或直接输入分类名称：')
        elif type == 'download':
            category = input('请输入要下载的指定分类：')
        elif type == 'check':
            category = input('请输入要查看的指定分类：')
        else:
            category = input('请输入要修改的分类序号或直接输入分类名称：')
        try:
            idx_num = int(category)
            return unique_categories[idx_num-1]
        except:
            return category


    def menu(self):
        """
        菜单
        """
        print('1.添加模块')
        print('2.修改模块')
        print('3.下载更新全部模块')
        print('4 下载更新指定分类的全部模块')
        print('5.下载更新指定模块')
        print('6.删除模块')
        print('7.查看当前所有模块信息')
        print('8.查看指定分类的模块信息')
        print('0.退出')
        
        action = input('请输入操作:')
        return action


    def show(self, mutiple=True):
        select_menu = {}
        modules_info = self.readJsonFile()
        if not modules_info:
            return None, None
        for idx, module in enumerate(modules_info):
            category = module.get('category','-')
            select_menu[f'{idx+1}'] = module
            print(f'{idx+1}. {module.get("name")} [{category}]')
        modules_name_l = []
        if mutiple:
            selected_nums = input('请选择模块，多选以空格隔开：')
            selected_list = [i for i in selected_nums.split(' ') if i != '']
            for i in selected_list:
                modules_name_l.append(select_menu.get(i))
        else:
            selected_nums = input('请选择单个模块：')
            modules_name_l.append(select_menu.get(selected_nums))
        
        return modules_name_l, modules_info
    
    # 查看模块信息
    def showAll(self, target_category=None):
        modules_info = self.readJsonFile()
        if not modules_info:
            return True
        for idx, module in enumerate(modules_info):
            if module.get('system'):
                if re.search('ios(?!&macos)', module.get('system'), re.IGNORECASE):
                    device = '📱'
                if re.search('(?<!ios&)macos', module.get('system'), re.IGNORECASE):
                    device = '🖥'
            else:   
                device = ''
                
            category = module.get('category')
            if category:
                category_info = f' [{category}]'
            else:
                category_info = ''

            if target_category and target_category != category:
                continue
            print(f'{idx+1}. {module["name"]} 🔗:{module["link"]} {device} {category_info}')

    # 遍历下载
    def threadDownload(self, target_category=None):
        modules_info = self.readJsonFile()
        if not modules_info:
            return True
        download_threads = []
        for module in modules_info:
            module_name, module_link, system, category = module['name'], module.get('link'), module.get('system'), module.get('category')
            t = Thread(target=self.download_module, args=(module_name, module_link, system, category))
            if target_category and target_category != category:
                continue
            download_threads.append(t)
        # 开始下载模块
        for t in download_threads:
            t.start()
        # 确保所有线程都下载完成以后再做文件处理
        for t in download_threads:
            t.join()
                
        print('模块下载更新处理完成')


    # 运行
    def run_process(self):
        # 菜单
        user_cmd = self.menu()
        if user_cmd == '1':
            self.add_links()
            return True
        elif user_cmd == '2':
            module_name_l, modules_info = self.show(mutiple=False)
            if not module_name_l:
                return True
            new_name = input(f'将{module_name_l[0]["name"]}的名称修改为(不输入则不更改)：')
            new_link = input(f'将{module_name_l[0]["name"]}的链接修改为(不输入则不更改)：')
            new_system = input(f'将{module_name_l[0]["name"]}的所属系统信息修改为(1为保持不变，0为移除系统信息，直接输入为更改信息)：')
            new_category = self.selectCategory(type='modify')
            
            wait_for_modify_index = modules_info.index(module_name_l[0])
            if new_link:
                modules_info[wait_for_modify_index]['link'] = new_link
            if new_system == '0':
                modules_info[wait_for_modify_index]['system'] = ''
            elif new_system and new_system != '1':
                modules_info[wait_for_modify_index]['system'] = new_system
            if new_category:
                modules_info[wait_for_modify_index]['category'] = new_category

            if new_name:
                modules_info[wait_for_modify_index]['name'] = new_name
                self.modifyFilename(module_name_l[0]["name"], new_name)


            self.saveJsonFile(modules_info)
            print(f'已修改')
            return True
        elif user_cmd == '3':
            self.threadDownload()
            return True
        elif user_cmd == '4':
            selected_cat = self.selectCategory(type='download')
            self.threadDownload(target_category=selected_cat)
            return True
        elif user_cmd == '5':
            module_name_l, modules_info = self.show()
            if not module_name_l:
                return True
            download_threads = []
            for name in module_name_l:
                for module in modules_info:
                    if module.get('name') == name:
                        module_name, module_link, system, category = name, module.get('link'), module.get('system'), module.get('category')
                        t = Thread(target=self.download_module, args=(module_name, module_link, system, category))
                        download_threads.append(t)
            # 开始下载模块
            for t in download_threads:
                t.start()
            # 确保所有线程都下载完成以后再做文件处理
            for t in download_threads:
                t.join()
                
            print('模块下载更新处理完成')
            return True
        elif user_cmd == '6':
            deleteinfocount = 0
            deletecount = 0
            module_name_l, modules_info = self.show()
            if not module_name_l:
                return True
            for module in module_name_l:
                modules_info.remove(module)
                deleteinfocount += 1
                    
                
                res = self.delete_module(module["name"])
                if res:
                    deletecount += 1
            if deleteinfocount > 0:
                self.saveJsonFile(modules_info)
                print(f'共删除{deleteinfocount}个模块信息/{deletecount}个模块')
            return True
        elif user_cmd == '7':
            self.showAll()
            return True
        elif user_cmd == '8':
            selected_cat = self.selectCategory(type='check')
            self.showAll(selected_cat)
            return True
        else:
            return False


def checkUpdate():
    script_origin = "https://raw.githubusercontent.com/BlackCCCat/SurgeModuleManager/main/ModuleDownloader_ios.py"
    res = requests.get(url=script_origin, verify=False)
    if res.status_code == 200 and 'text/plain' in res.headers.get('Content-Type'):
        new_version = re.search(r'#\s*version:(?P<version>\d+)', res.text).group("version")
        if new_version > __version__:
            user_ans = input("检查到新版本，是否更新(y/n)? ")
            if user_ans.lower() == 'y':
                with open(__file__, 'wb') as f:
                    f.write(res.text.encode())
                print('更新完成')
                return True
            else:
                return False
        else:
            return False
    else:
        print('无法获取最新版本')
        return False



def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.join(BASE_DIR,'Modules')
    
    check_res = checkUpdate()
    if check_res:
        print('请重新运行此脚本')
    else:
        surge = Process(BASE_DIR,module_dir)
        loop = True
        while loop:
            loop = surge.run_process()


if __name__ == "__main__":
    main()




