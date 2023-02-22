import jenkins
from utils.common_utils import request_url


class Jenkins(object):
  def __init__(self, host, username, password):
    self.host = host
    self.username = username
    self.password = password
    self.server = self.connect()

  def connect(self):
    return jenkins.Jenkins(self.host, username=self.username, password=self.password)

  def get_job_url(self, job_name):
    all_jobs = self.server.get_all_jobs()
    for job in all_jobs:
      if 'fullname' in job and job['fullname'] == job_name:
        return job['url'].replace('://', f'://{self.username}:{self.password}@')
    return ''

  def get_upstream_job_by_api(self, job_name, build_number):
    resp = request_url(f"{self.get_job_url(job_name)}/{build_number}/api/json")
    if resp:
      for action in resp.get('actions', []):
        causes = action.get('causes', [])
        for cause in reversed(causes) if causes else []:
          if cause.get('_class') in ['hudson.model.Cause$UpstreamCause',
                                     'org.jenkinsci.plugins.workflow.support.steps.build.BuildUpstreamCause']:
            return 'upstream', cause.get('upstreamProject'), int(cause.get('upstreamBuild'))
          if cause.get('_class') == 'com.sonyericsson.rebuild.RebuildCause':
            return 'rebuild', cause.get('upstreamProject'), int(cause.get('upstreamBuild'))
    # '' means it was caused by start/schedule instead of upstream.
    return '', job_name, int(build_number)

  def get_build_cause_chain(self, job_name, build_number):
    '''
    Get causes map of a build. Larger depth means more upstream build. Build_number in map is reversed.
    '''
    cause_map = {}
    depth = 0
    orig_job_name = job_name
    orig_build_number = build_number
    while not cause_map or orig_job_name != job_name or orig_build_number != build_number:
      cause, job_name, build_number = self.get_upstream_job_by_api(job_name, build_number)
      depth = depth + 1 if cause == 'upstream' else depth
      if depth not in cause_map:
        cause_map[depth] = {}
      if job_name in cause_map[depth]:
        cause_map[depth][job_name].append(build_number)
      else:
        cause_map[depth].update({job_name: [build_number]})
      if not cause:
        break
    return cause_map

  def get_build_artifacts(self, job_name, build_number):
    res = []
    try:
      build_info = self.server.get_build_info(job_name, build_number)
      if "artifacts" in build_info:
        for artifact in build_info["artifacts"]:
          res.append((artifact["fileName"], artifact["relativePath"]))
    except jenkins.JenkinsException as e:
      print(e)
    finally:
      return res
