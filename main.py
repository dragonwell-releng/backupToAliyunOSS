# This script should be triggerd by other project even if it was aborted.
import os
import sys

from utils.common_utils import get_config_from_yaml, create_directory, get_now_timestamp, exec_shell, remove_directory
from module.Jenkins import Jenkins
from module.AliyunOSS import AliyunOSS
from module.MultiThread import MultiThread


def main(jobs_map, aliyun_oss, jenkins):
  workdir = f'.cache/{get_now_timestamp()}'
  print(f"[DEBUG] workdir: {workdir}")
  print(f"[DEBUG] jobs_map: {jobs_map}")
  try:
    create_directory(workdir)
    jobs_list = sorted(jobs_map.items(), key=lambda key: key, reverse=True)
    prefix_path = ''
    thread_pool = MultiThread(10)  # excessive concurrency may cause download failure
    for depth, job in jobs_list:
      print(f"[DEBUG] processing depth={depth}, job={job}")
      if depth == 0:  # analysis project needn't be analyzed
        jobs_list.remove((depth, job))
        continue
      for job_name, build_numbers in job.items():
        build_number = build_numbers[0]
        prefix_path += f"{job_name.split('/')[-1]}/{build_number}/"
        print(f"[DEBUG] job_name={job_name}, build_number={build_number}, prefix_path={prefix_path}")
        if depth == 1:
          artifacts = jenkins.get_build_artifacts(job_name, build_number)
          print(f"[DEBUG] artifacts for {job_name}#{build_number}: {artifacts}")
          for artifact_basename, artifact_path in artifacts:
            if not artifact_basename.endswith('.tap'):
              print(f"[DEBUG] skip non-tap file: {artifact_basename}")
              continue
            job_url = jenkins.get_job_url(job_name)
            download_url = f'{job_url}/{build_number}/artifact/{artifact_path}'
            filename = artifact_basename.split('/')[-1]
            source = f"{workdir}/{filename}"
            target = filename  # 直接上传到 bucket 根目录，同名覆盖
            print(f"[DEBUG] download_url={download_url}")
            print(f"[DEBUG] source={source}, target={target}")
            thread_pool.run(download_and_upload,
                            username=jenkins.username,
                            password=jenkins.password,
                            url=download_url,
                            workdir=workdir,
                            aliyun_oss=aliyun_oss,
                            source=source,
                            target=target)
    thread_pool.join()
    if not thread_pool.res:
      return False
  except Exception as e:
    print(f"[ERROR] main exception: {e}")
  finally:
    remove_directory(workdir)


def download_and_upload(**kwargs):
  try:
    curl_cmd = f"curl --user {kwargs.get('username')}:{kwargs.get('password')} -OLJSk --retry 5 {kwargs.get('url')}"
    print(f"[DEBUG] curl cmd: {curl_cmd}")
    out, err, retc = exec_shell(curl_cmd, kwargs.get('workdir'))
    print(f"[DEBUG] curl retc={retc}, out={out}, err={err}")
    if retc != 0:
      print(f"[ERROR] curl failed with retc={retc}, err={err}")
      return False
    kwargs.get('aliyun_oss').upload_file(kwargs.get('source'), kwargs.get('target'))
    print(f"upload oss, file path: {kwargs.get('target')}")
    return True
  except Exception as e:
    print(f"[ERROR] download_and_upload exception: {e}")
    return False


if __name__ == '__main__':
  target_bucket = 'dragonwell-test-report'
  config_map = get_config_from_yaml('configure.yml')
  jenkins = Jenkins(config_map['jenkins']['host'], config_map['jenkins']['username'], config_map['jenkins']['password'])
  build_cause_chain = jenkins.get_build_cause_chain(os.getenv('JOB_NAME'), os.getenv('BUILD_NUMBER'))
  aliyun_account_name = config_map['aliyun']['oss'][target_bucket]['account']
  aliyun_account = config_map['aliyun']['account'][aliyun_account_name]
  aliyun_oss = AliyunOSS(aliyun_account['id'], aliyun_account['key'])
  bucket = aliyun_oss.get_bucket(target_bucket)
  if not bucket:
    print('Please create bucket by alibaba cloud account')
    sys.exit(1)
  main(build_cause_chain, aliyun_oss, jenkins)
