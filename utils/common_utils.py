import os
import shutil
import subprocess

import yaml
import requests
from datetime import datetime


def exec_shell(cmd, cwd=".", timeout=120, display=False):
  sb = subprocess.Popen(cmd,
                        cwd=cwd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True
                        )
  if display:
    print("exec shell command in {}: {}".format(cwd, cmd))
  out, err, retc = "", "", -999
  try:
    out, err = sb.communicate(timeout=timeout)
  except subprocess.TimeoutExpired:
    sb.kill()
  finally:
    retc = sb.returncode
    out = bytes.decode(out).strip() if isinstance(out, bytes) else out
    err = bytes.decode(err).strip() if isinstance(err, bytes) else err
    return out, err, retc


def get_config_from_yaml(filename):
  map = {}
  if not filename:
    return map
  with open(filename, "r", encoding="utf-8") as f:
    map.update(yaml.load(f, Loader=yaml.SafeLoader))
  return map


def request_url(url, headers={}, data={}, method='GET', to_json=True):
  resp = requests.request(method, url, headers=headers, data=data)
  if to_json:
    return resp.json() if resp else {}
  return resp.text if resp else ''


def create_directory(path, cover=True):
  if not path:
    return
  if cover and os.path.exists(path):
    shutil.rmtree(path)
  if not os.path.exists(path):
    os.makedirs(path)

def remove_directory(path):
  if path:
    shutil.rmtree(path)

def get_now_timestamp():
  return datetime.utcnow().strftime("%Y%m%d%H%M%S")
