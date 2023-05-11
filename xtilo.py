#! /usr/bin/env python3

# Copyright 2023-2024 by Xihihhh. All rights reserved.
# https://github.com/Xihihhh/xtilo has info about the project.
# https://github.com/Xihihhh/xtilo/blob/master/CONTRIBUTORS.md Thank you for help.

import os
import tarfile
import requests
import json
import hashlib
import io
import sys
from tqdm import tqdm
from prettytable import PrettyTable 
from bs4 import BeautifulSoup

XTILO_HOME = os.getenv('HOME') + '/.xtilo/'
XTILO_TMP  = XTILO_HOME + 'tmp/'
XTILO_CONFIG = XTILO_HOME + 'local.json'
XTILO_VERSION = '2.1.5'


def check_dir():
    if not os.path.isdir(XTILO_HOME):
        os.mkdir(XTILO_HOME)
    if not os.path.isdir(XTILO_TMP):
        os.mkdir(XTILO_TMP)


def check_arch():
    arch = os.uname().machine
    if arch == 'aarch64' or 'armv8' in arch:
        arch = 'aarch64'
    elif arch == 'x86_64':
        arch = 'amd64'
    elif '86' in arch:
        arch = 'i386'
    elif 'arm' in arch:
        arch = 'armhf'
    else:
        print('手机架构不受支持')
        sys.exit(1)
    return arch


def load_local():
    if not os.path.isfile(XTILO_CONFIG):
        with open(XTILO_CONFIG, 'w') as f:
            arch = check_arch()
            data = {
                'config': {
                    'arch': arch,
                    'version': XTILO_VERSION,
                    'imgList': 'https://raw.fastgit.org/Xihihhh/xtilo/master/src/list_cn.json'
                }
            }
            json.dump(data, f, indent=4)
    with open(XTILO_CONFIG, 'r') as f:
        config = json.load(f)
    return config


def set_list(url):
    if url == None:
        imgList = input('请输入新的镜像列表链接：')
        if imgList == '':
            print('未输入任何内容')
            sys.exit(1)
        else:
            config = load_local()
            config['config']['imgList'] = imgList
            with open(XTILO_CONFIG, 'w') as f:
                json.dump(config, f, indent=4)
            print('成功设置')
    else:
        config = load_local()
        config['config']['imgList'] = url
        with open(XTILO_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
        print('成功设置')


def get_list():
    try:
        imgList = load_local()['config']['imgList']
        r = requests.get(imgList)
    except requests.exceptions.ConnectionError:
        print('无法连接到 GitHub')
        print('请使用 xtilo set [镜像列表链接] 更换链接或代理')
        sys.exit(1)
    if not r.status_code == 200:
        print('无法获取镜像列表')
        sys.exit(1)
    return r.json()


def show_list():
    lists = get_list()
    config = load_local()
    table = PrettyTable()
    arch = check_arch()
    table.field_names = ['名称', '版本', '已安装', '可安装']
    for name in lists.get('linux'):
        infos = lists.get(name)
        version = infos.get('version')
        installed = name in config.keys()
        installable = arch in infos.keys()
        table.add_row([name, version, installed, installable])
    print(table.get_string())


def pull_image(distro):
    arch = check_arch()
    lists = get_list()
    config = load_local()
    distro_tmp = XTILO_TMP + distro
    if distro in config.keys():
        print('%s 已被安装' % distro)
        sys.exit(1)
    if distro not in lists.keys():
        print('未找到 %s' % distro)
        sys.exit(1)
    infos = lists.get(distro)
    if arch not in infos.keys():
        print('%s 不支持该架构' % distro)
        sys.exit(1)
    if infos.get('lxc'):
        time_stamp = get_lxc(infos.get(arch))
        url = '{0}{1}/rootfs.tar.xz'.format(infos.get(arch), time_stamp)
    else:
        url = infos.get(arch)
    if os.path.isfile(distro_tmp):
        print('%s 已缓存' % distro)
        print('跳过下载')
    else:
        print('拉取镜像中')
        r = requests.get(url, stream=True)
        if not r.status_code == 200:
            print('无法拉取镜像')
            print('网络错误')
            sys.exit(1)
        total_size = int(r.headers.get('Content-Length'))
        block_size = io.DEFAULT_BUFFER_SIZE
        t = tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(XTILO_TMP + distro, 'wb') as f:
            for chunk in r.iter_content(block_size):
                t.update(len(chunk))
                f.write(chunk)
        r.close()
        t.close()
    if infos.get('check') == 'no':
        print('%s 不支持校验' % distro)
        print('跳过校验')
    elif infos.get('check') == 'lxc':
        check_url = '{0}{1}/SHA256SUMS'.format(infos.get(arch), time_stamp)
        check_sum(distro=distro, url=check_url, check='sha256')
    else:
        check_url = url + '.' + infos.get('check')
        check_sum(distro=distro, url=check_url, check=infos.get('check'))
    if not infos.get('zip') == 'fedora':
        extract_file(distro, infos.get('zip'))
    else:
        extract_fedora()
    config_image(distro, infos)


def get_lxc(url):
    r = requests.get(url)
    if not r.status_code == 200:
        print('无法获取镜像链接')
        print('正在退出')
        sys.exit(1)
    soup = BeautifulSoup(r.text, 'html.parser')
    urls = soup.find_all('a')
    time_stamp = (urls[-1]).get('title')
    return time_stamp


def remove_image(distro):
    distro_path = XTILO_HOME + distro
    if os.path.isdir(distro_path):
        print('移除 %s 镜像' % distro)
        os.system('chmod -R 777 %s' % distro_path)
        os.system('rm -rf %s' % distro_path)
        script = '{0}start-{1}.sh'.format(XTILO_HOME, distro)
        if os.path.isfile(script):
            os.system('rm %s' % script)
        config = load_local()
        del config[distro]
        with open(XTILO_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
    else:
        print('未找到 %s 镜像' % distro)


def config_image(distro, infos):
    print('配置镜像中')
    distro_path = XTILO_HOME + distro
    resolv_conf = '{0}/etc/resolv.conf'.format(distro_path)
    if os.path.islink(resolv_conf):
        os.unlink(resolv_conf)
    with open(resolv_conf, 'w') as f:
        f.write('nameserver 223.5.5.5\n')
        f.write('nameserver 223.6.6.6\n')
    group = distro_path + '/etc/group'
    with os.popen('whoami') as p:
        userid = p.read()
        userid = userid[4 : len(userid) - 1]
        gp1 = '20' + userid
        gp2 = '50' + userid
    with open(group, 'a') as g:
        g.write('''
3003:x:3003:
9997:x:9997:
{0}:x:{0}:
{1}:x:{1}:'''.format(gp1, gp2))
    config = load_local()
    config.update({distro: infos})
    with open(XTILO_CONFIG, 'w') as f:
        json.dump(config, f, indent=4)
    script(distro)
    print('一切完成')
    print('使用 xtilo run %s 来运行' % distro)


def script(distro):
    distro_path = XTILO_HOME + distro
    infos = load_local().get(distro)
    script = '{0}start-{1}.sh'.format(XTILO_HOME, distro)
    with open(script, 'w') as s:
        s.write("""#!/usr/bin/bash
unset LD_PRELOAD
command='proot'
command+=' --link2symlink'
command+=' -S'
command+=' %s' % distro_path
#command+=' -b /storage/emulated/0'
#command+=' -b /sdcard'
#command+=' -b /data/data/com.termux'
#command+=' -b /system'
command+=' -w /root'
command+=' /usr/bin/env -i'
command+=' HOME=/root'
command+=' LANG=C.UTF-8'
command+=' PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
command+=' TERM=xterm-256color'
command+=' /bin/'
command+='""" % distro_path)
        if 'shell' in infos.keys():
            s.write(infos.get('shell'))
        else:
            s.write('bash')
        s.write("""'
command+=' --login'
$command""")
        os.system('chmod +x %s' % script)
        print('启动脚本已生成')


def extract_file(distro, zip_m):
    distro_path = XTILO_HOME + distro
    file_path = XTILO_TMP + distro
    if os.path.isdir(distro_path):
        os.system('chmod -R 777 %s' % distro_path)
        os.system('rm -rf %s' % distro_path)
    zip_f = tarfile.open(file_path, 'r:' + zip_m)
    if not os.path.isdir(distro_path):
        os.mkdir(distro_path)
    print('解压镜像中')
    zip_f.extractall(distro_path, numeric_owner=True)


def extract_fedora():
    file_path = XTILO_TMP + 'fedora'
    distro_path = XTILO_HOME + 'fedora'
    print('解压镜像中')
    zip_f = tarfile.open(file_path)
    for i in zip_f.getnames():
        if 'layer.tar' in i:
            zip_name = i
    zip_f.extract(zip_name, XTILO_TMP)
    zip_f.close()
    zip_f = tarfile.open(XTILO_TMP + zip_name, 'r')
    if not os.path.isdir(distro_path):
        os.mkdir(distro_path)
    zip_f.extractall(distro_path, numeric_owner=True)


def check_sum(distro, url, check):
    print('校验文件完整性')
    r = requests.get(url)
    file_path = XTILO_TMP + distro
    if not r.status_code == 200:
        a = input('无法获取文件校验码，是否继续 [y/n] ')
        if a not in ('y', 'Y'):
            print('正在退出')
            os.remove(file_path)
            sys.exit(1)
        else:
            return
    sum_calc = hashlib.md5() if check == 'md5' else  hashlib.sha256()
    total_size = os.path.getsize(file_path)
    block_size = io.DEFAULT_BUFFER_SIZE
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(block_size ), b''):
            t.update(len(chunk))
            sum_calc.update(chunk)
    t.close()
    f.close()
    if sum_calc.hexdigest() in r.text:
        print('文件校验成功')
        return 0
    else:
        print('文件校验失败')
        print('正在退出')
        os.remove(file_path)
        sys.exit(1)


def check_sum_ubuntu(distro, url):
    r = requests.get(url)
    file_path = XTILO_TMP + distro
    if not r.status_code == 200:
        a = input('无法获取文件校验码，是否继续 [y/n] ')
        if a not in ('y','Y'):
            print('正在退出')
            os.remove(file_path)
            sys.exit(1)
    sum_calc = hashlib.md5()
    total_size = os.path.getsize(file_path)
    block_size = io.DEFAULT_BUFFER_SIZE
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            t.update(len(chunk))
            sum_calc.update(chunk)
    t.close()
    f.close()
    if sum_calc.hexdigest() in r.text:
        return 0
    else:
        print('文件校验失败')
        print('正在退出')
        os.remove(file_path)
        sys.exit(1)


def clean_tmps():
    print('正在清除缓存')
    os.system('rm -rf {0}*'.format(XTILO_TMP))


def run_image(distro):
    config = load_local()
    if distro not in config.keys():
        print('未在本地找到 %s 镜像' % distro)
        sys.exit(1)
    distro_path = XTILO_HOME + distro
    infos = config.get(distro)
    command = ['proot']
    command.append(' --link2symlink')
    command.append(' -S')
    command.append(distro_path)
   #command.append(' -b /storage/emulated/0')
   #command.append(' -b /sdcard')
   #command.append(' -b /data/data/com.termux')
   #command.append(' -b /system')
    command.append(' -w /root')
    command.append(' /usr/bin/env -i')
    command.append(' HOME=/root')
    command.append(' LANG=C.UTF-8')
    command.append(' PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin')
    command.append(' TERM=xterm-256color')
    command.append(' /bin/')
    os.unsetenv('LD_PRELOAD')
    if 'shell' in infos.keys():
        command.append(infos.get('shell'))
    else:
        command.append('bash')
    command.append(' --login')
    os.system(''.join(command))


def show_help():
    print('Xtilo\t\t', XTILO_VERSION)
    print('Usage: xtilo [命令] [参数]\n')
    print('Xtilo 是一个用来帮助你在 termux 上安装不同的 GNU/Linux 发行版的程序')
    print('它由 Xihi 修改自 Atilo\n')
    print('命令：')
    print('images\t\t 列出可用镜像')
    print('set\t\t 设置镜像列表链接')
    print('remove\t\t 移除本地的镜像')
    print('pull\t\t 拉取远程的镜像')
    print('run\t\t 运行镜像')
    print('clean\t\t 清除缓存')
    print('help\t\t 帮助\n')


if __name__ == '__main__':
    check_dir()
    if len(sys.argv) == 1:
        show_help()
        print('请指定一个命令')
        sys.exit(1)
    if len(sys.argv) > 3:
        print('无用参数')
        sys.exit(1)
    if sys.argv[1] == 'help':
        show_help()
    elif sys.argv[1] == 'set':
        if len(sys.argv) == 3:
            set_list(sys.argv[2])
        else:
            set_list(None)
    elif sys.argv[1] == 'pull':
        if len(sys.argv) == 2:
            print('你需要从镜像列表中指定可用镜像')
            sys.exit(1)
        else:
            pull_image(sys.argv[2])
    elif sys.argv[1] == 'images':
        show_list()
    elif sys.argv[1] == 'remove':
        if len(sys.argv) == 2:
            print('你需要从镜像列表中指定可用镜像')
            sys.exit(1)
        else:
            remove_image(sys.argv[2])
    elif sys.argv[1] == 'run':
        if len(sys.argv) == 2:
            print('你需要从镜像列表中指定可用镜像')
            sys.exit(1)
        else:
            run_image(sys.argv[2])
    elif sys.argv[1] == 'clean':
        clean_tmps()
    else:
        print('未知命令')
        sys.exit(1)
