
import os
import errno
import random
import string


class EfiUtils:

    def mkdir_p(path):
        """
        _mkdir_p: make directory for given path
        """
        if not path:
            return
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def object_info_to_ref(object_info):
        print(object_info)
        if object_info == None or len(object_info) == 0:
            return None
        else:
            object_info = object_info[0]
            return f'{object_info[6]}/{object_info[0]}/{object_info[4]}'

    def get_unique_dir(base_dir, dir_suffix = ''):
        new_dir = os.path.join(base_dir, dir_suffix + EfiUtils.id_generator(8))
        while os.path.exists(new_dir):
            new_dir = os.path.join(base_dir, dir_prefix + EfiUtils.id_generator(8))
        return new_dir

    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

