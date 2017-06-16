import http.client
import logging
import os
import shlex
import subprocess
from urllib import parse

logger = logging.getLogger("UTILS")
logger.setLevel(logging.DEBUG)


def get_num(x):
    return int(''.join(ele for ele in x if ele.isdigit() or ele == '.'))


def run_command(command):
    process = subprocess.Popen(shlex.split(command), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = str(process.stdout.readline())
        if process.poll() is not None:
            break
        if output and len(output) > 6:
            logger.info(str(output).lstrip('b').replace('\\n', ''))

    rc = process.poll()
    return rc


def folder_size(path, excludes):
    try:
        process = os.popen(du_size_command(path, excludes))
        data = process.read()
        process.close()
        if data is not None and int(data) > 0:
            return int(data)

    except Exception as ex:
        logger.exception("Exception calculating size of %r: ", path)
        return None


def rclone_delete(path):
    try:
        process = os.popen('rclone delete "%s"' % path)
        data = process.read()
        process.close()
        if 'Failed to delete' in data:
            return False
        else:
            return True
    except Exception as ex:
        logger.exception("Exception deleting %r: ", path)
        return False


def opened_files(path, excludes):
    files = []

    try:
        process = os.popen('lsof -Fn +D "%s" | tail -n +2 | cut -c2-' % path)
        data = process.read()
        process.close()
        for item in data.split('\n'):
            if not item or len(item) <= 2 or os.path.isdir(item):
                continue
            if not item.isdigit():
                for exclude in excludes:
                    if exclude.lower() in item.lower():
                        continue
                files.append(item)

        return files

    except Exception as ex:
        logger.exception("Exception checking %r: ", path)
        return None


def send_pushover(app_token, user_token, message):
    try:
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json", parse.urlencode({
            'token': app_token,
            'user': user_token,
            'message': message
        }), {"Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        conn.close()
        return True if resp.status == 200 else False

    except Exception as ex:
        logger.exception("Error sending notification to %r", user_token)
    return False


def rclone_move_command(local, remote, transfers, checkers, excludes):
    upload_cmd = 'rclone move "%s" "%s"' \
                 ' --delete-after' \
                 ' --no-traverse' \
                 ' --stats=60s' \
                 ' -v' \
                 ' --transfers=%d' \
                 ' --checkers=%d' % \
                 (local, remote, transfers, checkers)
    for item in excludes:
        upload_cmd += ' --exclude="%s"' % item
    return upload_cmd


def du_size_command(path, excludes):
    size_cmd = "du -s --block-size=1G"
    for item in excludes:
        size_cmd += ' --exclude="%s"' % item
    size_cmd += ' "%s" | cut -f1' % path
    return size_cmd