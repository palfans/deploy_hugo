#!python
# coding:utf-8

import os
import sys
import glob
import time
import locale
import shutil
import argparse
import win32api
import subprocess

__author__ = 'Palfans'

GIT_REPO = [
    ['origin', 'code', 'git@github.com:palfans/palfans.github.io.git'],
]

DEPLOY_REPO = [
    ['origin', 'master', 'git@github.com:palfans/palfans.github.io.git'],
]

BASE_URL = 'https://www.palfans.net/'


class ChDir:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.newPath = os.path.expanduser(new_path)

    def __enter__(self):
        self.savedPath = os.getcwd()
        if not os.path.exists(self.newPath):
            os.makedirs(self.newPath)
        os.chdir(self.newPath)

    def __exit__(self, exception_type, exception_value, traceback):
        os.chdir(self.savedPath)


def git_init(dir, repos):
    git_dir = os.path.join(dir, '.git')
    if not os.path.exists(git_dir):
        subprocess.call('git init', shell=True)
        if len(repos) > 0:
            for repo in repos:
                subprocess.call(
                    'git remote add {0} {1}'.format(repo[0], repo[2]),
                    shell=True)


def git_pull(repos):
    if len(repos) > 0:
        subprocess.call('git fetch {0}'.format(repos[0][0]), shell=True)
        subprocess.call('git checkout {0}'.format(repos[0][1]), shell=True)
        subprocess.call(
            'git reset --hard {0}/{1}'.format(repos[0][0], repos[0][1]),
            shell=True)
        subprocess.call('git clean -df', shell=True)
        subprocess.call('git submodule init', shell=True)
        subprocess.call('git submodule update', shell=True)
        subprocess.call(
            'git submodule foreach git pull --rebase origin master',
            shell=True)


def get_workdir(args):
    if args.work_dir:
        work_dir = args.work_dir
    else:
        work_dir = os.path.dirname(os.path.abspath(__file__))

    return work_dir


def compose(args):
    current_dir = get_workdir(args)

    with ChDir(current_dir):
        git_init(current_dir, GIT_REPO)
        git_pull(GIT_REPO)
        article_time = time.strftime('%Y-%m-%d', time.localtime())

        if args.article_title:
            article_title = article_time + '-' + args.article_title
        else:
            article_title = article_time + '-untitled'
        subprocess.call(
            'hugo new post/{0}.md'.format(article_title), shell=True)

        link_path = current_dir + '\\content\\post\\img'
        img_path = current_dir + '\\static\\img'

        article_path = current_dir + '\\content\\post\\' + article_title + '.md'
        subprocess.call(
            'mklink /D {0} {1}'.format(link_path, img_path), shell=True)
        subprocess.call('pip install pywin32', shell=True)
        win32api.ShellExecute(0, 'open', article_path, '', '', 1)


def deploy(args):
    current_dir = get_workdir(args)
    deploy_dir = os.path.join(current_dir, 'public')

    with ChDir(current_dir):
        if len(GIT_REPO) > 0:
            subprocess.call('git add --all', shell=True)
            subprocess.call(
                'git commit -a -m "{0}"'.format('upt: new article'),
                shell=True)
            for repo in GIT_REPO:
                if args.test:
                    print('git push {0} {1}'.format(repo[0], repo[1]))
                else:
                    subprocess.call(
                        'git push {0} {1}'.format(repo[0], repo[1]),
                        shell=True)

    if args.manual:
        if args.base_url:
            base_url = args.base_url
        else:
            base_url = BASE_URL

        subprocess.call('hugo -v --baseURL=' + base_url, shell=True)
        
        with ChDir(deploy_dir):
            git_init(deploy_dir, DEPLOY_REPO)
            git_pull(DEPLOY_REPO)

            if len(DEPLOY_REPO) > 0:

                subprocess.call('git add --all', shell=True)
                subprocess.call(
                    'git commit -a -m "{0}"'.format('upt: new article'),
                    shell=True)
                for repo in DEPLOY_REPO:
                    if args.test:
                        print('git push {0} {1}'.format(repo[0], repo[1]))
                    else:
                        subprocess.call(
                            'git push {0} {1}'.format(repo[0], repo[1]),
                            shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compose article and deploy Hugo')
    parser.add_argument('type', help='compose or deploy')
    parser.add_argument(
        '-d',
        dest='work_dir',
        action='store',
        help='set work directory, current path if empty')
    parser.add_argument(
        '-t', dest='test', action='store_true', help='for test')
    parser.add_argument('-v', action='version', version='%(prog)s 1.0')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    compose_grp = parser.add_argument_group(title='compose options')
    deploy_grp = parser.add_argument_group(title='deploy options')
    compose_grp.add_argument(
        '-a', dest='article_title', action='store', help='set article title')
    deploy_grp.add_argument(
        '-b', dest='base_url', action='store', help='set base url')
    deploy_grp.add_argument(
        '-m', dest='manual', action='store_true', help='deploy manually')
    args = parser.parse_args()

    if args.type in ['compose']:
        compose(args)
    elif args.type in ['deploy']:
        deploy(args)
