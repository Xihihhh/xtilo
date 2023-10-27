# Xtilo

帮助你在 Termux 上安装 GNU/Linux 发行版的程序。修改自[atilo](https://github.com/YadominJinta/atilo)

## 依赖

``` bash
pkg install -y curl proot python
python -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --upgrade pip
pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple requests tqdm prettytable beautifulsoup4
```

## 安装

``` bash
cd
curl -O https://gitee.com/xihihhh/xtilo/raw/master/xtilo.py
# curl -O https://github.com/Xihihhh/xtilo/raw/master/xtilo.py
mv xtilo.py xtilo
chmod +x xtilo
```

## 使用方法

``` bash
Xtilo           2.2.1
Usage: xtilo [命令] [参数]

Xtilo 是一个用来帮助你在 Termux 上安装不同的 GNU/Linux 发行版的程序

命令:
images           列出可用镜像
set              设置镜像列表链接
remove           移除本地的镜像
pull             拉取远程的镜像
run              运行镜像
clean            清除缓存
help             帮助
```

## 支持的发行版

| 发行版             | aarch64 |  arm  | x86_64 | i386  |
| ------------------ | :-----: | :---: | :----: | :---: |
| Alpine Linux       |    √    |   √   |   √    |   √   |
| Arch Linux         |    √    |   ×   |   √    |   ×   |
| CentOS Linux       |    √    |   ×   |   √    |   ×   |
| CentOS Stream      |    √    |   ×   |   √    |   ×   |
| Debian             |    √    |   ×   |   √    |   ×   |
| Devuan             |    √    |   ×   |   √    |   ×   |
| Fedora Linux       |    √    |   ×   |   √    |   ×   |
| Kali Linux         |    √    |   ×   |   √    |   ×   |
| openSUSE           |    √    |   ×   |   √    |   ×   |
| Ubuntu             |    √    |   ×   |   √    |   ×   |
| Void Linux         |    √    |   ×   |   √    |   ×   |

## 图形

[在termux上开启图形化](https://yadominjinta.github.io/2018/07/30/GUI-on-termux.html)

## 相关项目

**[EXALAB/AnLinux-App](https://github.com/EXALAB/AnLinux-App)**: APP to help install Linux on termux.  
**[sdrausty/TermuxArch](https://github.com/sdrausty/TermuxArch)**: Arch install script  
**[Neo-Oli/termux-ubuntu](https://github.com/Neo-Oli/termux-ubuntu)**: Ubuntu chroot on termux  
**[Hax4us/Nethunter-In-Termux](https://github.com/Hax4us/Nethunter-In-Termux)**: Install Kali nethunter (Kali Linux) in your termux application without rooted phone  
**[nmilosev/termux-fedora](https://github.com/nmilosev/termux-fedora)**: A script to install a Fedora chroot into Termux  
**[sp4rkie/debian-on-termux](https://github.com/sp4rkie/debian-on-termux)**: Install Debian 11 (bullseye) on your Android smartphone
**[Hax4us/TermuxAlpine](https://github.com/Hax4us/TermuxAlpine)**: Use TermuxAlpine.sh calling to install Alpine Linux in Termux on Android

**[Proot简明手册](https://github.com/myfreess/Mytermuxdoc/wiki/Proot)**:帮助Termux用户编写proot脚本的简明指南