#!/usr/bin/env python3

# Copyright 2023-2024 by Xihihhh. All rights reserved.
# https://gitee.com/Xihihhh/xtilo has info about the project.
# https://github.com/YadominJinta/atilo/blob/master/CONTRIBUTORS.md Thank you for help.

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

FILE_NAME = os.path.basename(__file__)
XTILO_HOME = f"{os.getenv('HOME')}/.xtilo/"
XTILO_TMP  = f'{XTILO_HOME}tmp/'
XTILO_CONFIG = f'{XTILO_HOME}local.json'
XTILO_VERSION = '2.2.1'


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
                    'imgList': 'https://gitee.com/xihihhh/xtilo/raw/master/src/list_cn.json'
                }
            }
            json.dump(data, f, indent=4)
    with open(XTILO_CONFIG, 'r') as f:
        config = json.load(f)
    return config


def set_list(url):
    if url:
        config = load_local()
        config['config']['imgList'] = url
        with open(XTILO_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
        print('成功设置')
    else:
        imgList = input('请输入新的镜像列表链接：')
        if imgList:
            config = load_local()
            config['config']['imgList'] = imgList
            with open(XTILO_CONFIG, 'w') as f:
                json.dump(config, f, indent=4)
            print('成功设置')
        else:
            print('未输入任何内容')
            sys.exit(1)


def get_list():
    try:
        imgList = load_local()['config']['imgList']
        r = requests.get(imgList)
    except requests.exceptions.ConnectionError:
        print('无法获取镜像列表')
        print(f'请使用 {FILE_NAME} set [镜像列表链接] 更换链接')
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
    table.field_names = ['名称', '版本', '别名', '已安装', '可安装']
    for alias in lists.get('linux'):
        infos = lists.get(alias)
        name = infos.get('name')
        version = infos.get('version')
        installed = alias in config.keys()
        installable = arch in infos.keys()
        table.add_row([name, version, alias, installed, installable])
    print(table.get_string())


def pull_image(distro):
    arch = check_arch()
    lists = get_list()
    config = load_local()
    distro_tmp = XTILO_TMP + distro
    if distro in config.keys():
        print(f'{distro} 已被安装')
        sys.exit(1)
    if distro not in lists.keys():
        print(f'未找到 {distro}')
        sys.exit(1)
    infos = lists.get(distro)
    if arch not in infos.keys():
        print(f'{distro} 不支持该架构')
        sys.exit(1)
    if infos.get('lxc'):
        time_stamp = get_lxc(infos.get(arch))
        url = f'{infos.get(arch)}{time_stamp}/rootfs.tar.xz'
    else:
        url = infos.get(arch)
    if os.path.isfile(distro_tmp):
        print(f'{distro} 已缓存')
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
        print(f'{distro} 不支持校验')
        print('跳过校验')
    elif infos.get('check') == 'lxc':
        check_url = f'{infos.get(arch)}{time_stamp}/SHA256SUMS'
        check_sum(distro=distro, url=check_url, check='sha256')
    else:
        check_url = f"{url}.{infos.get('check')}"
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
        print(f'移除 {distro} 镜像')
        os.system(f'chmod -R 777 {distro_path}')
        os.system(f'rm -rf {distro_path}')
        script = f'{XTILO_HOME}start-{distro}.sh'
        if os.path.isfile(script):
            os.system(f'rm {script}')
        config = load_local()
        del config[distro]
        with open(XTILO_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
    else:
        print(f'未找到 {distro} 镜像')


def config_image(distro, infos):
    print('配置镜像中')
    distro_path = XTILO_HOME + distro
    proc = f'{distro_path}/proc/'
    os.system(f'mkdir -p {proc}')
    os.system(f'chmod 700 {proc}')
    with open(f'{proc}.uptime', 'w') as u:
        u.write('124.08 932.80\n')
    with open(f'{proc}.loadavg', 'w') as l:
        l.write('0.12 0.07 0.02 2/165 765\n')
    with open(f'{proc}.version', 'w') as v:
        v.write(f'Linux version {XTILO_VERSION}-Xtilo\n')
    with open(f'{proc}.stat', 'w') as s:
        s.write('''cpu  1957 0 2877 93280 262 342 254 87 0 0
cpu0 31 0 226 12027 82 10 4 9 0 0
cpu1 45 0 664 11144 21 263 233 12 0 0
cpu2 494 0 537 11283 27 10 3 8 0 0
cpu3 359 0 234 11723 24 26 5 7 0 0
cpu4 295 0 268 11772 10 12 2 12 0 0
cpu5 270 0 251 11833 15 3 1 10 0 0
cpu6 430 0 520 11386 30 8 1 12 0 0
cpu7 30 0 172 12108 50 8 1 13 0 0
intr 127541 38 290 0 0 0 0 4 0 1 0 0 25329 258 0 5777 277 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
ctxt 14022
btime 1680020856
processes 772
procs_running 2
procs_blocked 0
softirq 75663 0 5903 6 25375 10774 0 243 11685 0 21677
''')
    with open(f'{proc}.vmstat', 'w') as vm:
        vm.write('''nr_free_pages 1743136
nr_zone_inactive_anon 179281
nr_zone_active_anon 7183
nr_zone_inactive_file 22858
nr_zone_active_file 51328
nr_zone_unevictable 642
nr_zone_write_pending 0
nr_mlock 0
nr_bounce 0
nr_zspages 0
nr_free_cma 0
numa_hit 1259626
numa_miss 0
numa_foreign 0
numa_interleave 720
numa_local 1259626
numa_other 0
nr_inactive_anon 179281
nr_active_anon 7183
nr_inactive_file 22858
nr_active_file 51328
nr_unevictable 642
nr_slab_reclaimable 8091
nr_slab_unreclaimable 7804
nr_isolated_anon 0
nr_isolated_file 0
workingset_nodes 0
workingset_refault_anon 0
workingset_refault_file 0
workingset_activate_anon 0
workingset_activate_file 0
workingset_restore_anon 0
workingset_restore_file 0
workingset_nodereclaim 0
nr_anon_pages 7723
nr_mapped 8905
nr_file_pages 253569
nr_dirty 0
nr_writeback 0
nr_writeback_temp 0
nr_shmem 178741
nr_shmem_hugepages 0
nr_shmem_pmdmapped 0
nr_file_hugepages 0
nr_file_pmdmapped 0
nr_anon_transparent_hugepages 1
nr_vmscan_write 0
nr_vmscan_immediate_reclaim 0
nr_dirtied 0
nr_written 0
nr_throttled_written 0
nr_kernel_misc_reclaimable 0
nr_foll_pin_acquired 0
nr_foll_pin_released 0
nr_kernel_stack 2780
nr_page_table_pages 344
nr_sec_page_table_pages 0
nr_swapcached 0
pgpromote_success 0
pgpromote_candidate 0
nr_dirty_threshold 356564
nr_dirty_background_threshold 178064
pgpgin 890508
pgpgout 0
pswpin 0
pswpout 0
pgalloc_dma 272
pgalloc_dma32 261
pgalloc_normal 1328079
pgalloc_movable 0
pgalloc_device 0
allocstall_dma 0
allocstall_dma32 0
allocstall_normal 0
allocstall_movable 0
allocstall_device 0
pgskip_dma 0
pgskip_dma32 0
pgskip_normal 0
pgskip_movable 0
pgskip_device 0
pgfree 3077011
pgactivate 0
pgdeactivate 0
pglazyfree 0
pgfault 176973
pgmajfault 488
pglazyfreed 0
pgrefill 0
pgreuse 19230
pgsteal_kswapd 0
pgsteal_direct 0
pgsteal_khugepaged 0
pgdemote_kswapd 0
pgdemote_direct 0
pgdemote_khugepaged 0
pgscan_kswapd 0
pgscan_direct 0
pgscan_khugepaged 0
pgscan_direct_throttle 0
pgscan_anon 0
pgscan_file 0
pgsteal_anon 0
pgsteal_file 0
zone_reclaim_failed 0
pginodesteal 0
slabs_scanned 0
kswapd_inodesteal 0
kswapd_low_wmark_hit_quickly 0
kswapd_high_wmark_hit_quickly 0
pageoutrun 0
pgrotated 0
drop_pagecache 0
drop_slab 0
oom_kill 0
numa_pte_updates 0
numa_huge_pte_updates 0
numa_hint_faults 0
numa_hint_faults_local 0
numa_pages_migrated 0
pgmigrate_success 0
pgmigrate_fail 0
thp_migration_success 0
thp_migration_fail 0
thp_migration_split 0
compact_migrate_scanned 0
compact_free_scanned 0
compact_isolated 0
compact_stall 0
compact_fail 0
compact_success 0
compact_daemon_wake 0
compact_daemon_migrate_scanned 0
compact_daemon_free_scanned 0
htlb_buddy_alloc_success 0
htlb_buddy_alloc_fail 0
cma_alloc_success 0
cma_alloc_fail 0
unevictable_pgs_culled 27002
unevictable_pgs_scanned 0
unevictable_pgs_rescued 744
unevictable_pgs_mlocked 744
unevictable_pgs_munlocked 744
unevictable_pgs_cleared 0
unevictable_pgs_stranded 0
thp_fault_alloc 13
thp_fault_fallback 0
thp_fault_fallback_charge 0
thp_collapse_alloc 4
thp_collapse_alloc_failed 0
thp_file_alloc 0
thp_file_fallback 0
thp_file_fallback_charge 0
thp_file_mapped 0
thp_split_page 0
thp_split_page_failed 0
thp_deferred_split_page 1
thp_split_pmd 1
thp_scan_exceed_none_pte 0
thp_scan_exceed_swap_pte 0
thp_scan_exceed_share_pte 0
thp_split_pud 0
thp_zero_page_alloc 0
thp_zero_page_alloc_failed 0
thp_swpout 0
thp_swpout_fallback 0
balloon_inflate 0
balloon_deflate 0
balloon_migrate 0
swap_ra 0
swap_ra_hit 0
ksm_swpin_copy 0
cow_ksm 0
zswpin 0
zswpout 0
direct_map_level2_splits 29
direct_map_level3_splits 0
nr_unstable 0
''')
    resolv_conf = f'{distro_path}/etc/resolv.conf'
    if os.path.islink(resolv_conf):
        os.unlink(resolv_conf)
    with open(resolv_conf, 'w') as f:
        f.write('nameserver 223.5.5.5\n')
        f.write('nameserver 223.6.6.6\n')
    group = f'{distro_path}/etc/group'
    with os.popen('whoami') as p:
        userid = p.read()
        userid = userid[4 : len(userid) - 1]
    with open(group, 'a') as g:
        g.write(f'''
3003:x:3003:
9997:x:9997:
20{userid}:x:20{userid}:
50{userid}:x:50{userid}:
''')
    if distro in ('arch', 'kali') or 'debian' in distro:
        with open(f'{distro_path}/etc/bash.bashrc', 'a') as rc:
            rc.write('''
alias ls='ls --color=auto'
alias grep='grep --color=auto'
''')
    config = load_local()
    config.update({distro: infos})
    with open(XTILO_CONFIG, 'w') as f:
        json.dump(config, f, indent=4)
    script(distro)
    print('一切完成')
    print(f'使用 {FILE_NAME} run {distro} 来运行')


def script(distro):
    distro_path = XTILO_HOME + distro
    infos = load_local().get(distro)
    script = f'{XTILO_HOME}start-{distro}.sh'
    with open(script, 'w') as s:
        s.write(f"""#!/usr/bin/bash
DISTRO_PATH={distro_path}
unset LD_PRELOAD
command='proot'
command+=' --link2symlink'
command+=' --kill-on-exit'
command+=' -S '
command+=$DISTRO_PATH
command+=' --cwd=/root'
#command+=" -b $TMPDIR:/tmp"
#command+=' -b /storage'
#command+=' -b /sdcard'
#command+=' -b /data/data/com.termux'
#command+=' -b /vendor'
#if [ -d '/apex' ]; then
#    command+=' -b /apex'
#fi
#command+=' -b /system'
command+=' -b /dev'
command+=' -b /dev/urandom:/dev/random'
command+=" -b $DISTRO_PATH/root:/dev/shm"
command+=' -b /proc'
command+=' -b /proc/self/fd:/dev/fd'
command+=' -b /proc/self/fd/0:/dev/stdin'
command+=' -b /proc/self/fd/1:/dev/stdout'
command+=' -b /proc/self/fd/2:/dev/stderr'
command+=' -b /sys'
command+=" -b $DISTRO_PATH/proc/.loadavg:/proc/loadavg"
command+=" -b $DISTRO_PATH/proc/.stat:/proc/stat"
command+=" -b $DISTRO_PATH/proc/.uptime:/proc/uptime"
command+=" -b $DISTRO_PATH/proc/.version:/proc/version"
command+=" -b $DISTRO_PATH/proc/.vmstat:/proc/vmstat"
command+=' -w /root'
command+=' /usr/bin/env -i'
command+=' HOME=/root'
command+=' LANG=C.UTF-8'
command+=' PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
command+=' TERM=xterm-256color'
command+=' TMPDIR=/tmp'
command+=' /bin/'
command+='""")
        if 'shell' in infos.keys():
            s.write(infos.get('shell'))
        else:
            s.write('bash')
        s.write("""'
command+=' --login'
com="$@"
if [ -e $1 ]; then
    exec $command
else
    $command -e "$com"
fi
""")
        os.system(f'chmod +x {script}')
        print('启动脚本已生成')


def extract_file(distro, zip_m):
    distro_path = XTILO_HOME + distro
    file_path = XTILO_TMP + distro
    if os.path.isdir(distro_path):
        os.system(f'chmod -R 777 {distro_path}')
        os.system(f'rm -rf {distro_path}')
    zip_f = tarfile.open(file_path, f'r:{zip_m}')
    if not os.path.isdir(distro_path):
        os.mkdir(distro_path)
    print('解压镜像中')
    zip_f.extractall(distro_path, numeric_owner=True)


def extract_fedora():
    file_path = f'{XTILO_TMP}fedora'
    distro_path = f'{XTILO_HOME}fedora'
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
        a = input('无法获取文件校验码，是否继续 [Y/*] ')
        if a not in ('Y', 'y'):
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
        for chunk in iter(lambda: f.read(block_size), b''):
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
        a = input('无法获取文件校验码，是否继续 [Y/*] ')
        if a not in ('Y','y'):
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
    os.system(f'rm -rf {XTILO_TMP}*')


def run_image(distro, com):
    config = load_local()
    if distro not in config.keys():
        print(f'未在本地找到 {distro} 镜像')
        sys.exit(1)
    distro_path = XTILO_HOME + distro
    infos = config.get(distro)
    command = ['proot']
    command.append(' --link2symlink')
    command.append(' --kill-on-exit')
    command.append(' -S ')
    command.append(distro_path)
    command.append(' --cwd=/root')
    #command.append(f' -b {distro_path}:/tmp')
    #command.append(' -b /storage')
    #command.append(' -b /sdcard')
    #command.append(' -b /data/data/com.termux')
    #command.append(' -b /vendor')
    #if os.path.isdir('/apex'):
        #command.append(' -b /apex')
    #command.append(' -b /system')
    command.append(' -b /dev')
    command.append(' -b /dev/urandom:/dev/random')
    command.append(f' -b {distro_path}/root:/dev/shm')
    command.append(' -b /proc')
    command.append(' -b /proc/self/fd:/dev/fd')
    command.append(' -b /proc/self/fd/0:/dev/stdin')
    command.append(' -b /proc/self/fd/1:/dev/stdout')
    command.append(' -b /proc/self/fd/2:/dev/stderr')
    command.append(' -b /sys')
    command.append(f' -b {distro_path}/proc/.loadavg:/proc/loadavg')
    command.append(f' -b {distro_path}/proc/.stat:/proc/stat')
    command.append(f' -b {distro_path}/proc/.uptime:/proc/uptime')
    command.append(f' -b {distro_path}/proc/.version:/proc/version')
    command.append(f' -b {distro_path}/proc/.vmstat:/proc/vmstat')
    command.append(' -w /root')
    command.append(' /usr/bin/env -i')
    command.append(' HOME=/root')
    command.append(' LANG=C.UTF-8')
    command.append(' PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin')
    command.append(' TERM=xterm-256color')
    command.append(' TMPDIR=/tmp')
    command.append(' /bin/')
    os.unsetenv('LD_PRELOAD')
    if 'shell' in infos.keys():
        command.append(infos.get('shell'))
    else:
        command.append('bash')
    command.append(' --login')
    if com:
        os.system(f"""{''.join(command)} -c '{' '.join(com)}'""")
    else:
        os.system(f"exec {''.join(command)}")


def show_help():
    print('Xtilo\t\t', XTILO_VERSION)
    print(f'Usage: {FILE_NAME} [命令] [参数]\n')
    print('Xtilo 是一个用来帮助你在 Termux 上安装不同的 GNU/Linux 发行版的程序')
    print('修改自 Atilo\n')
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
    if len(sys.argv) > 3 and sys.argv[1] != 'run':
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
            run_image(sys.argv[2], sys.argv[3:] if len(sys.argv) > 3 else None)
    elif sys.argv[1] == 'clean':
        clean_tmps()
    else:
        print('未知命令')
        sys.exit(1)