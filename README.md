# 说明
自用！自用！自用！
重要的事情说三遍，能用就行的脚本，就不要嫌弃了。

**Surge模块管理脚本的Python版本**
对于Surge这个网络代理软件，已有很多用不同语言实现模块管理的“小程序”，如快捷指令（iOS）、JavaScript（iOS端app：Scriptable）等，本脚本为Python实现，单独有可在iOS端pythonista运行的版本

# 使用
- 下载或复制脚本内容到Surge配置文件所在的路径下的`.py`文件中
-  在Mac上：`python ModuleDownloader.py`
-  在iOS上：在pythonista中打开并运行


选择添加模块时，需注意格式为`name@links[@sysinfo]`，`[@sysinfo]`为可选内容，即系统信息，分为`iOS`和`Mac`两种值，不区分大小写