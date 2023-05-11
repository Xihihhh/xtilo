# Xtilo

在Termux安装Linux。修改自[YadominJinta/atilo](https://github.com/YadominJinta/atilo)

## 依赖

``` bash
pkg install proot python wget -y
```

## 安装

``` bash
wget https://raw.njuu.cf/Xihihhh/xtilo/master/xtilo.py
```

## 使用方法

``` bash
Xtilo           2.1.5
Usage: xtilo [命令] [参数]

Xtilo 是一个用来帮助你在 termux 上安装不同的 GNU/Linux 发行版的程序

命令:
images           列出可用镜像
remove           移除本地的镜像
pull             拉取远的镜像
run              运行镜像
clean            清除缓存
help             帮助
```

## 支持的发行版

| 发行版        | aarch64 |  arm  | x86_64 | i386  |
| ------------- | :-----: | :---: | :----: | :---: |
| Alpine        |    √    |   √   |   √    |   √   |
| CentOS7       |    √    |   √   |   √    |   √   |
| CentOS-Stream8|    √    |   ×   |   √    |   ×   |
| CentOS-Stream9|    √    |   ×   |   √    |   ×   |
| Debian        |    √    |   √   |   √    |   √   |
| Devuan        |    √    |   √   |   √    |   √   |
| Fedora        |    √    |   ×   |   √    |   ×   |
| Kali          |    √    |   √   |   √    |   ×   |
| openSUSE      |    √    |   ×   |   √    |   ×   |
| Ubuntu        |    √    |   √   |   √    |   ×   |

## 图形

[在termux上开启图形化](https://yadominjinta.github.io/2018/07/30/GUI-on-termux.html)

## 相关项目

**[EXALAB/AnLinux-App](https://github.com/EXALAB/AnLinux-App)**: APP to help install Linux on termux.  
**[sdrausty/TermuxArch](https://github.com/sdrausty/TermuxArch)**: Arch install script  
**[Neo-Oli/termux-ubuntu](https://github.com/Neo-Oli/termux-ubuntu)**: Ubuntu chroot on termux  
**[Hax4us/Nethunter-In-Termux](https://github.com/Hax4us/Nethunter-In-Termux)**: Install Kali nethunter (Kali Linux) in your termux application without rooted phone  
**[nmilosev/termux-fedora](https://github.com/nmilosev/termux-fedora)**: A script to install a Fedora chroot into Termux  
**[sp4rkie/debian-on-termux](https://github.com/sp4rkie/debian-on-termux)**: Install Debian 9 (stretch) on your Android smartphone
**[Hax4us/TermuxAlpine](https://github.com/Hax4us/TermuxAlpine)**: Use TermuxAlpine.sh calling to install Alpine Linux in Termux on Android

**[Proot简明手册](https://github.com/myfreess/Mytermuxdoc/wiki/Proot)**:帮助Termux用户编写proot脚本的简明指南
