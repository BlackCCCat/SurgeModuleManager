# -*- coding: utf-8 -*-
# version:20250102

__version__ = "20250102"

import os
import requests
import re
import json

import warnings
from urllib3.exceptions import InsecureRequestWarning


# 禁用警告
warnings.filterwarnings("ignore", category=InsecureRequestWarning)
# 在使用 requests 库进行 HTTPS 请求之前禁用警告
requests.packages.urllib3.disable_warnings()

import urllib3
urllib3.disable_warnings()

class Process(object):    
    def __init__(self, module_info_dir, module_dir):
        # 初始化模块信息路径和模块存储路径
        self.module_info_dir = module_info_dir
        self.module_dir = module_dir
        self.check()
        
    def check(self):
        """
        检查模块信息文件和模块存储路径是否存在，不存在则创建
        """
        if not os.path.isfile(self.module_info_dir):
            with open(self.module_info_dir, 'w') as f:
                f.write('')
        
        if not os.path.isdir(self.module_dir):
            os.makedirs(self.module_dir)

    def readJsonFile(self) -> list:
        """
        读取modules.json
        """
        with open(self.module_info_dir, 'r') as f:
            content = f.read()

        try:
            modules = json.loads(content)
        except:
            modules = []
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
        exists_names = []
        for item in modules_info:
            exists_links.append(item["link"])
            exists_names.append(item["name"])
        
            
        if new_url in exists_links:
            url_check = 1
        if new_name in exists_names:
            name_check = 1
        
        return url_check, name_check

    # 添加模块及下载链接
    def add_module(self, module:dict):
        """
        param module: dict: {'name': name, 'link': link, 'system': system, 'category': category}
        添加新的模块
        """
        modules_info = self.readJsonFile()

        if module:
            add_module_name = module["name"]
            add_module_link = module["link"]
            add_module_sysinfo = module["system"]
            add_module_category = module["category"]
            if self.exists_links(add_module_link, add_module_name, modules_info):
                modules_info.append(module)
                self.saveJsonFile(modules_info)
                # 下载模块
                download_res = self.download_module(module)
                if download_res:
                    return True
        return False
         
    # 下载
    def download_module(self, module: dict):
        module_name, module_link, system_info, module_category = module["name"], module["link"], module["system"], module["category"]
        try:
            res = requests.get(module_link,verify=False)
        except:
            res = None
        if not res:
            return False
        if res.status_code == 200 and ('text/plain' in res.headers.get('Content-Type') or 'application/octet-stream' in res.headers.get('Content-Type')):
            if '🔗' not in res.text:
                # modify the content
                new_content = re.sub(r'#!\s*name\s*=', '#!name=🔗', res.text)
                
            if system_info:
                if re.search('ios(?!&macos)',system_info,re.IGNORECASE):
                    sysinfo = '#!system=ios\n'
                elif re.match('(?<!ios&)macos',system_info,re.IGNORECASE):
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
            with open(whole_file_name,'w') as mf:
                mf.write(all_content)

            return True
        return False
        
    # 修改文件名
    def modifyFilename(self, old_name, new_name):
        modules_list = os.listdir(self.module_dir)
        old_module_name, new_module_name = old_name + '.sgmodule', new_name + '.sgmodule'
        if old_module_name in modules_list:
            os.rename(os.path.join(self.module_dir, old_module_name), os.path.join(self.module_dir, new_module_name))
            return True
        return False

    # 删除模块信息及文件
    def delete_module(self, module):
        modules_info = self.readJsonFile()
        modules_info.remove(module)
        self.saveJsonFile(modules_info)

        module_name = module["name"]
        file_name = module_name + '.sgmodule'
        remove_module_dir = os.path.join(self.module_dir, file_name)
        if os.path.exists(remove_module_dir):
            os.remove(remove_module_dir)
            return True

    def getCategories(self) -> list:
        """
        获取分类信息
        """
        categories = []
        modules_info = self.readJsonFile()

        for item in modules_info:
            category_info = item.get("category")
            if category_info:
                categories.append(category_info)

        unique_categories = list(set(categories))
        return unique_categories

