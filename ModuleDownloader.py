# -*- coding: utf-8 -*-
# version:20240317

__version__ = "20240317"

import os
import sys
import requests
import re
import json
from threading import Thread

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
        
    def check(self):
        if not os.path.isfile(self.module_info_dir):
            with open(self.module_info_dir, 'w') as f:
                f.write('')
        
        if not os.path.isdir(self.module_dir):
            os.makedirs(self.module_dir)

    def readJsonFile(self):
        """
        读取modules.json
        """
        with open(self.module_info_dir, 'r') as f:
            content = f.read()
        
        try:
            modules = json.loads(content)
        except:
            print('当前无模块信息')
            modules = {}
        return modules
        
    def saveJsonFile(self, modules_info):
        """
        保存到modules.json
        """
        modules_info_str = json.dumps(modules_info, ensure_ascii=False, indent=4)
        with open(self.module_info_dir, 'w') as f:
            f.write(modules_info_str)
            # json.dump(modules_info, f, ensure_ascii=False, indent=4)
    
    def exists_links(self,new_url,new_name,modules_info):
        """
        判断链接及定义的文件名称是否已存在
        """
        url_check, name_check = 0, 0

        exists_links = []
        for key, value in modules_info.items():
            exists_links.append(value)
        
            
        if new_url in exists_links:
            url_check = 1
        if new_name in modules_info.keys():
            name_check = 1
        
        return url_check, name_check

    # 添加模块及下载链接
    def add_links(self):
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
                        modules_info[add_module_name] = {'link':add_module_link,'system':add_module_sysinfo}
                        count += 1
                    else:
                        print('当前系统下名称重复')
                else:
                    print('链接已存在')
            else:
                loop = False

        self.saveJsonFile(modules_info)

        print(f'共添加{count}个模块下载链接')

    # 下载
    def download_module(self,module_name,module_link,system_info):
        res = requests.get(module_link,verify=False)
        if res.status_code == 200 and 'text/plain' in res.headers.get('Content-Type'):# 响应状态是成功并且内容是文本
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
                

            # 写入指定路径并以module_name命名
            file_name = module_name + '.sgmodule'
            whole_file_name = os.path.join(self.module_dir,file_name)
            with open(whole_file_name,'w') as mf:
                mf.write(res_content)

            print(f'✅ {module_name}(链接为:{module_link}) 已下载')
            return True
        elif res.status_code == 404:
            print(f'🈳 {module_name}(链接为:{module_link}) 不存在，请检查GitHub地址是否正确')
        else:
            print(f'❌ 下载 {module_name}(链接为:{module_link}) 失败')
            return False


    def menu(self):
        """
        菜单
        """
        print('1.添加模块')
        print('2.修改模块')
        print('3.下载更新全部模块')
        print('4.下载更新指定模块')
        print('5.删除模块')
        print('6.查看当前模块信息')
        print('0.退出')
        
        action = input('请输入操作:')
        return action


    def show(self, mutiple=True):
        select_menu = {}
        modules_info = self.readJsonFile()
        for idx, k in enumerate(modules_info):
            select_menu[f'{idx+1}'] = k
            print(f'{idx+1}. {k}')
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




    # 运行
    def run_process(self):
        # 菜单
        user_cmd = self.menu()
        if user_cmd == '1':
            self.add_links()
            return True
        elif user_cmd == '2':
            module_name_l, modules_info = self.show(mutiple=False)
            new_name = input(f'将{module_name_l[0]}的名称修改为(不输入则不更改)：')
            new_link = input(f'将{module_name_l[0]}的链接修改为(不输入则不更改)：')
            new_system = input(f'将{module_name_l[0]}的所属系统信息修改为(不输入则不更改)：')
            
            if new_link:
                modules_info[module_name_l[0]]['link'] = new_link
            if new_system:
                modules_info[module_name_l[0]]['system'] = new_link
            if new_name:
                modules_info.update({new_name: modules_info.pop(module_name_l[0])})
            
            self.saveJsonFile(modules_info)
            print(f'已修改')
            return True
        elif user_cmd == '3':
            modules_info = self.readJsonFile()
            download_threads = []
            for k in modules_info:
                module_name, module_link, system = k, modules_info[k].get('link'), modules_info[k].get('system')
                t = Thread(target=self.download_module, args=(module_name, module_link, system))
                download_threads.append(t)
            # 开始下载模块
            for t in download_threads:
                t.start()
            # 确保所有线程都下载完成以后再做文件处理
            for t in download_threads:
                t.join()
                
            print('模块下载更新处理完成')
            return True
        elif user_cmd == '4':
            module_name_l, modules_info = self.show()
            download_threads = []
            for name in module_name_l:
                module_name, module_link, system = name, modules_info.get(name).get('link'), modules_info.get(name).get('system')
                t = Thread(target=self.download_module, args=(module_name, module_link, system))
                download_threads.append(t)
            # 开始下载模块
            for t in download_threads:
                t.start()
            # 确保所有线程都下载完成以后再做文件处理
            for t in download_threads:
                t.join()
                
            print('模块下载更新处理完成')
            return True
        elif user_cmd == '5':
            deleteinfocount = 0
            deletecount = 0
            module_name_l, modules_info = self.show()
            for name in module_name_l:
                if modules_info.get(name):
                    modules_info.pop(name)
                    
                    deleteinfocount += 1
                
                file_name = name + '.sgmodule'
                remove_module_dir = os.path.join(self.module_dir, file_name)
                if os.path.exists(remove_module_dir):
                    os.remove(remove_module_dir)
                    deletecount += 1
            if deleteinfocount > 0:
                self.saveJsonFile(modules_info)
                print(f'共删除{deleteinfocount}个模块信息/{deletecount}个模块')
            return True
        elif user_cmd == '6':
            modules_info = self.readJsonFile()
            for idx, k in enumerate(modules_info):
                if modules_info[k].get('system'):
                    if re.search('(?i)ios',modules_info[k].get('system')):
                        device = '📱'
                    if re.search('(?i)mac',modules_info[k].get('system')):
                        device = '🖥'
                else:   
                    device = ''
                print(f'{idx+1}. {k} 🔗:{modules_info[k]["link"]} {device}')
            return True
        else:
            return False


def checkUpdate():
    script_origin = "https://raw.githubusercontent.com/BlackCCCat/SurgeModuleManager/main/ModuleDownloader.py"
    res = requests.get(url=script_origin, verify=False)
    new_script_content = res.text
    new_version = re.search('^#version:(?P<version>\d+)', res.text).group("version")
    if new_version > __version__:
        user_ans = input("检查到新版本，是否更新？y/n")
        if user_ans.lower() == 'y':
            with open(__file__, 'w') as f:
                f.write(res.text)
            print('更新完成')
            return True
        else:
            return False
    else:
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




