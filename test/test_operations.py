import os
import sys
import logging

src_path = os.path.realpath(__file__)
src_dir = os.path.dirname(src_path)
sys.path.append(os.path.join(src_dir, "../"))

from lib.operations import *


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def test_01_register_channel():
    register_channel(12345, 12345)
    print(list_channels()[0])

    register_channel(12345, 12343)
    print(list_channels()[0])

    register_channel(12345, 12340)
    print(list_channels()[0])

    register_channel(12345, 12341)
    print(list_channels()[0])

def test_02_add_user():
    add_user(12345, "hogehoge", 36500, "superchanllenge")
    print(list_users()[0])

