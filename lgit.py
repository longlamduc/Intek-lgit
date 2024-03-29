#!/usr/bin/env python3
import argparse
import os
import hashlib
import shutil
import datetime
# update git init


def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='+', help='init/add/commit/snapshots/'
                        'index/config/status')
    parser.add_argument('--author', action='store')
    parser.add_argument('-m', action='store')
    args = parser.parse_args()
    return args


def main():
    args = get_argument()
    content_index = []
    command = args.command[0]
    author = os.environ['LOGNAME']
    path_dir = os.getcwd()
    init = 0
    flag = 0
    while path_dir != '/' and flag == 0:
        for root, dirnames, filenames in os.walk(path_dir):
            if flag == 0:
                for name in dirnames:
                    if name == '.lgit':
                        init = 1
                        path_lgit = path_dir
                        flag = 1
                        break
        path_dir = os.path.dirname(path_dir)
    if command == 'init':
        create_dir()
        init = 1
    elif init == 0:
        print('fatal: not a git repository (or any of the parent'
              ' directories)')
    elif init == 1:
        if command == 'add':
            argument = args.command[1:]
            flag = 1
            for item in argument:
                if not os.path.exists(item):
                    print("fatal: pathspec '" + item +
                          "' did not match any files")
                    flag = 0
                    break
            if flag == 1:
                for item in argument:
                    list_index = lgit_add(path_lgit, item)
                    content_index = add_list(list_index, content_index)
                write_index_content(path_lgit, content_index)
        elif command == 'rm':
            argument = args.command[1:]
            for item in argument:
                if not os.path.exists(item):
                    print("fatal: pathspec '" + item +
                          "' did not match any files")
                    break
                else:
                    update_index = remove_index(path_lgit, item)
                    if update_index == 0:
                        print("fatal: pathspec '" + item +
                              "' did not match any files")
                    else:
                        write_index(path_lgit, '\n'.join(update_index) + '\n')
                        remove_file(item)
        elif command == 'config':
            author = args.author
            config(path_lgit, args.author)
        elif command == 'commit':
            # not do fatal error of commit: not init
            with open(path_lgit + '/.lgit/config', 'r') as file:
                author = file.readline().strip()
            lgit_commit(path_lgit, args.m, author)
        elif command == 'ls-files':
            print_ls_files(path_lgit)
        elif command == 'status':
            status_list, commit = get_status(path_lgit)
            print_status(status_list, commit)
        elif command == 'log':
            lgit_log(path_lgit)


def lgit_log(path_lgit):
    list_files = []
    path = path_lgit + '/.lgit/commits'
    for dirname, dirnames, filenames in os.walk(path):
        for name in filenames:
            list_files.append(name)
    list_files.sort(reverse=True)
    for i in list_files:
        with open(path + "/" + i, "r") as file:
            lines = file.readlines()
        print('commit', i)
        print('Author:', lines[0].strip())
        time = datetime.datetime.strptime(lines[1].strip(), '%Y%m%d%H%M%S')
        print('Date:', time.strftime('%a %b %d %H:%M:%S %Y'))
        print()
        print('\t' + lines[3] + '\n')


# -------------------------------LGIT STATUS-----------------------------------
def get_status(path_lgit):
    status_list = [[], [], []]  # [to be committed][not staged][untracked]
    if len(os.listdir(path_lgit + '/.lgit/commits')) == 0:
        commit = 0
    else:
        commit = 1
    with open(path_lgit + '/.lgit/index', 'r') as file:
        line = file.readlines()
    files = []
    for x in range(len(line)):
        line[x] = line[x][:-1].split(' ')
        line[x][1] = caculate_sha1_file(path_lgit+'/'+line[x][-1])
        if line[x][2] != line[x][3]:
            status_list[0].append(line[x][-1])
        if line[x][1] != line[x][2]:
            status_list[1].append(line[x][-1])
        files.append(line[x][-1])
    with open(path_lgit + '/.lgit/index', 'w') as file:
        for x in line:
            file.write(' '.join(x) + '\n')
    list_file = []
    pre_path = os.getcwd().split(path_lgit)[-1][1:]
    if len(pre_path) > 0:
        pre_path += '/'
    for dirname, dirnames, filenames in os.walk('./'):
        for filename in filenames:
            path = os.path.join(dirname, filename)
            if '.lgit' not in path and '.git' not in path:
                list_file.append(pre_path + path[2:])
    for file in list_file:
        if file not in files:
            status_list[2].append(file)
    return status_list, commit


def print_status(status_list, commit):
    print('On branch master')
    if commit == 0:
        print('\nNo commits yet\n')
    if status_list[0]:
        print('Changes to be committed:')
        print('  (use "./lgit.py reset HEAD ..." to unstage)\n')
        for x in status_list[0]:
            print('\t modified: ' + x)
        print()
    if status_list[1]:
        print('Changes not staged for commit:')
        print('  (use "./lgit.py add ..." to update what will be committed)')
        print('  (use "./lgit.py checkout -- ..." to discard changes in'
              ' working directory)\n')
        for x in status_list[1]:
            print('\t modified: ' + x)
        print()
    if status_list[2]:
        print('Untracked files:')
        print('  (use "./lgit.py add <file>..." to include in what will'
              ' be committed)\n')
        for x in status_list[2]:
            print('\t' + x)
        print('\nnothing added to commit but untracked files'
              ' present (use "./lgit.py add" to track)\n')


# -------------------------------LGIT LS-FILES---------------------------------
def print_ls_files(path_lgit):
    path = os.getcwd()
    list_file = []
    list_result = []
    with open(path_lgit + "/.lgit/index", "r") as f_index:
        lines = f_index.readlines()
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            list_file.append(os.path.join(dirname, filename))
    for line in lines:
        path_index = (line.split(' ')[-1]).strip()
        for path1 in list_file:
            if path_index in path1:
                index = path1.split(path)[-1][1:]
                if index not in list_result:
                    list_result.append(index)
    list_result = sorted(list_result)
    print('\n'.join(list_result))


def check_directory(path):  # ?????
    path_dir = path
    flag = 0
    while flag != 1:
        for root, dirnames, filenames in os.walk(path_dir):
            for name in dirnames:
                if name == '.lgit':
                    return path_dir
        path_dir = os.path.dirname(path_dir)


# -------------------------------LGIT RM-------------------------------------
def remove_file(filename):
    path_list = filename
    basename = os.path.basename(filename)
    if os.path.exists(filename):
        os.remove(filename)


def remove_index(path_lgit, filename):
    # find pathname_deleted in index and rm file # (2)
    update_index = []
    flag = 0
    with open(path_lgit + "/.lgit/index", "r") as f_index:
        lines = f_index.readlines()
    for line in lines:
        path = (line.split(' ')[-1]).strip()
        if filename == path:
            flag = 1
        if filename != path:
            update_index.append(line.strip())
    if flag == 0:
        return flag  # if not have turn 0
    else:
        return update_index  # if have turn list are deleted file index


def write_index_content(path_lgit, content):
    with open(path_lgit + '/.lgit/index', 'r+') as file:
        lines = file.readlines()
    for line_content in content:
        path_name = line_content.split(' ')[-1]
        flag = 0
        for i in range(len(lines)):
            lines[i] = lines[i].strip()
            path_index = lines[i].split(' ')[-1]
            if path_name == path_index:
                lines[i] = lines[i].split(' ')
                lines[i][1] = lines[i][2] = line_content.split(' ')[1]
                lines[i][0] = line_content.split(' ')[0]
                lines[i] = ' '.join(lines[i])
                flag = 1
        if flag == 0:
            lines.append(line_content)
    write_index(path_lgit, '\n'.join(lines) + '\n')


# -------------------------------LGIT COMMIT----------------------------------
def lgit_commit(path_lgit, mess, author):
    check = 0
    with open(path_lgit + '/.lgit/index', 'r+') as file:
        lines = file.readlines()
    for x in range(len(lines)):
        subline = []
        for y in lines[x].split(' '):
            if y != '':
                subline.append(y)
        if len(subline) == 4:
            subline.insert(3, subline[2])
            check = 1
        elif subline[3] != subline[2]:
            subline[3] = subline[2]
            check = 1
        lines[x] = ' '.join(subline)
    if check == 1:
        with open(path_lgit + '/.lgit/index', 'w+') as file:
            file.write(''.join(lines))
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")
        with open(path_lgit + '/.lgit/commits/' + time, 'w+') as file:
            file.write(author + '\n')
            file.write(time.split('.')[0] + '\n\n')
            file.write(mess + '\n')
        with open(path_lgit + '/.lgit/snapshots/' + time, 'w+') as f:
            for line in lines:
                f.write(line.split(' ')[3] + ' ' + line.split(' ')[4])
    elif check == 0:
        print('On branch master')
        print("Your branch is up-to-date with 'origin/master'.")
        print('nothing to commit, working directory clean')


# -------------------------------LGIT CONFIG--AUTHOR---------------------------
def config(path_lgit, author):
    file = path_lgit + '/.lgit/config'
    with open(file, 'w+') as f:
        f.write(author + '\n')


def write_index(path_lgit, content):  # write file index # (1)
    with open(path_lgit + "/.lgit/index", 'w') as f_index:
        f_index.write(content)
    f_index.close()


# -------------------------------LGIT ADD----------------------------------
def lgit_add(path_lgit, file_name):
    list_index = []
    if os.path.isdir(file_name):
        files = directory_tree_list(file_name)
        for file in files:
            index = create_file_objects(path_lgit, file)
            list_index.append(index)
    if os.path.isfile(file_name):
        index = create_file_objects(path_lgit, file_name)
        list_index.append(index)
    return list_index


def directory_tree_list(path):
    list_file = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            list_file.append(os.path.join(dirname, filename))
    return list_file


def create_file_objects(path_lgit, filename):
    file_content = open(filename, 'r').read()
    path_objects = path_lgit + '/.lgit/objects'
    hash_sha1 = caculate_sha1_file(filename)
    file_name = hash_sha1[2:]
    dir_name = hash_sha1[:2]
    if not os.path.exists(path_objects + "/" + dir_name):
        os.mkdir(path_objects + "/" + dir_name)
    file = open(path_objects + "/" + dir_name + "/" + file_name, 'w+')
    file.write(file_content)
    file.close()
    hash_sha2 = caculate_sha1_file(path_objects + "/" + dir_name + "/"
                                   + file_name)
    index = create_structure_index(path_lgit, filename, hash_sha1, hash_sha2)
    return(index)


def add_list(list, list_add):  # (3)
    for i in list:
        if '.lgit' not in i and '.git' not in i:
            list_add.append(i)
    return list_add


def caculate_sha1_file(filename):
    with open(filename, 'rb') as file:
        text = b''.join(file.readlines())
    hash_object = hashlib.sha1(text)
    hex_dig = hash_object.hexdigest()
    return hex_dig


def create_structure_index(path_lgit, filename, hash1, hash2):
    file_index = []
    timestamp = str(get_timestamp(filename))
    file_index.append(timestamp)
    file_index.append(hash1)
    file_index.append(hash2)
    # SHA1 of the file content after commited
    file_index.append(' ' * 40)
    path = os.getcwd().split(path_lgit)[-1][1:]
    if len(path) > 0:
        path += '/'
    if filename[:2] == './':
        file_index.append(path + filename[2:])
    else:
        file_index.append(path + filename)
    return ' '.join(file_index)


def get_timestamp(filename):
    t = os.path.getmtime(filename)
    time = str(datetime.datetime.fromtimestamp(t))
    stamp = datetime.datetime.fromtimestamp(t).timestamp() * 1000
    list1 = time.split('.')
    time = list1[0]
    list_time = list(time)
    timestamp = []
    for i in list_time:
        if i != '-' and i != ':' and i != ' ':
            timestamp.append(i)
    return(''.join(timestamp))


# --------------------------------INIT---------------------------------
def create_dir():
    path = os.getcwd() + '/.lgit'
    if os.path.exists(path):
        print('Git repository already initialized.')
    else:
        os.mkdir(path)
        os.mkdir(path + '/commits')
        os.mkdir(path + '/objects')
        os.mkdir(path + '/snapshots')
        filename_index = os.path.join(path, 'index')
        file = open(filename_index, 'w+')
        file.close()
        filename_config = os.path.join(path, 'config')
        file = open(filename_config, 'w+')
        file.write(os.environ['LOGNAME'])
        file.close()


if __name__ == '__main__':
    main()
