import oss2
from itertools import islice


class AliyunOSS(object):
  def __init__(self, account_id, account_key):
    self.id = account_id
    self.key = account_key
    self.auth = self.login(self.id, self.key)
    self.bucket = None

  def login(self, id, key):
    return oss2.Auth(id, key)

  def get_bucket(self, bucket_name, endpoint='http://oss-cn-hangzhou.aliyuncs.com'):
    try:
      self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
    except Exception as e:
      self.bucket = None
    finally:
      return self.bucket

  def create_bucket(self, bucket_name='', endpoint='http://oss-cn-hangzhou.aliyuncs.com'):
    bucket = self.get_bucket(bucket_name, endpoint) if bucket_name else self.bucket
    res = bucket.create_bucket(oss2.models.BUCKET_ACL_PUBLIC_READ_WRITE)
    return res.status

  def upload_file(self, source, target, bucket_name='', endpoint='http://oss-cn-hangzhou.aliyuncs.com'):
    bucket = self.get_bucket(bucket_name, endpoint) if bucket_name else self.bucket
    res = bucket.put_object_from_file(target, source)
    return res.status

  def download_file(self, source, target, bucket_name='', endpoint='http://oss-cn-hangzhou.aliyuncs.com'):
    bucket = self.get_bucket(bucket_name, endpoint) if bucket_name else self.bucket
    res = bucket.get_object_to_file(source, target)
    return res.status

  def list_objects(self, bucket_name='', endpoint='http://oss-cn-hangzhou.aliyuncs.com', max_num=50):
    bucket = self.get_bucket(bucket_name, endpoint) if bucket_name else self.bucket
    return [obj for obj in islice(oss2.ObjectIterator(bucket), max_num)]

  def remove_objects(self, bucket_name, path, prefix='', endpoint='http://oss-cn-hangzhou.aliyuncs.com'):
    bucket = self.get_bucket(bucket_name, endpoint) if bucket_name else self.bucket
    if not prefix:
      if path:
        return (bucket.delete_object(path)).status
      return False
    res = True
    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
      res = (bucket.delete_object(obj.key)).status and res
    return res
