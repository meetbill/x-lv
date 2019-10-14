#!/usr/bin/python
# coding=utf8
"""
# Author: meetbill
# Created Time : 2019-10-13 14:52:13

# File Name: tail.py
# Description:

"""
"""SYS LIBS
"""
import os
import sys
import time
import threading
import traceback
import logging

# Good behaviors. It means refusing called like from xxx import *
# When `__all__` is []
__all__ = []

reload(sys)
sys.setdefaultencoding('utf-8')


# ********************************************************
# * Global defines start.                                *
# ********************************************************


# ********************************************************
# * Global defines end.                                  *
# ********************************************************


class Tail(object):

    """
    Python-Tail - Unix tail follow implementation in Python.

    python-tail can be used to monitor changes to a file.

    Example:
        import tail

        # Create a tail instance
        t = tail.Tail('file-to-be-followed')

        # Register a callback function to be called when a new line is found in the followed file.
        # If no callback function is registerd, new lines would be printed to standard out.
        t.register_callback(callback_function)

        # Follow the file with 5 seconds as sleep time between iterations.
        # If sleep time is not provided 1 second is used as the default time.
        t.follow(s=5)
    """

    ''' Represents a tail command. '''

    def __init__(self, tailed_file, last_pos=0):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed.
                last_pos - 程序上一次停止时读取的最后位置，主要用于重启时恢复上次读取的位置，
                           防止数据丢失
        '''

        self.check_file_validity(tailed_file)
        self.tailed_file = tailed_file
        self.callback = sys.stdout.write
        self.last_pos = int(last_pos)

        self.try_count = 0
        self.read_try = 0

        self.event = threading.Event()
        self.event.clear()

        try:
            self.file_ = open(self.tailed_file, "r")
            self.size = os.path.getsize(self.tailed_file)

            if self.last_pos == 0:
                # Go to the end of file
                self.file_.seek(0, 2)
            else:
                # Go to the last position
                self.file_.seek(self.last_pos)
        except Exception as e:
            raise TailError(str(e))

    def reload_tailed_file(self):
        """ Reload tailed file when it be empty be `echo "" > tailed file`, or
            segmentated by logrotate.
        """
        try:
            self.file_.close()
            self.file_ = open(self.tailed_file, "r")
            self.size = os.path.getsize(self.tailed_file)

            # Go to the head of file
            self.file_.seek(0)

            return True
        except Exception as e:
            err_msg = {"type": -1,
                       "msg": "Error when reload file, detail: %s" % e}
            logging.error(err_msg)
            return False

    def update_filesize(self):
        # 获取文件大小成功时，说明有此文件
        try:
            _size = os.path.getsize(self.tailed_file)
        except Exception as e:
            err_msg = {"type": -1,
                       "msg": "Error when get size of '%s', detail: %s" % (self.tailed_file, e)}
            logging.error(err_msg)
            self.try_count += 1

            if self.try_count == 20:
                msg = "Error, try open '%s' failed after '%d' times" % (self.tailed_file,
                                                                        self.try_count)
                err_msg = {"type": -2,
                           "msg": msg}
                logging.error(err_msg)
                self.event.set()
            else:
                time.sleep(0.2)
            return False
        else:
            self.try_count = 0

        if _size >= self.size:
            self.size = _size
        else:
            msg = "File '%s' is changed" % self.tailed_file
            err_msg = {"type": -1,
                       "msg": msg}
            logging.error(err_msg)

            if not self.reload_tailed_file():
                self.event.set()
                return False
        return True

    def follow(self, s=0.01):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            s - Number of seconds to wait between each iteration; Defaults to 0.01. """

        self.event.clear()

        while not self.event.isSet():
            # (1) 更新记录的文件大小(如果记录的文件大小比获取的文件大小大，说明文件发生过改变)
            # (2) 记录文件读取指针的位置(字节数)
            # (3) 读取文件一行内容
            # (4) 如果读取的内容为空，或者读取的内容不是完整一行，则将读取指针移动到上次读取处

            if not self.update_filesize():
                continue
            try:
                curr_position = self.file_.tell()
                line = self.file_.readline()

                if not line:
                    self.file_.seek(curr_position)
                elif not line.endswith("\n"):
                    self.file_.seek(curr_position)
                else:
                    #err_msg = {"type": 2, "msg": (self.file_.tell(), self.size)}
                    # logging.info(err_msg)
                    self.callback(line)

                self.read_try = 0
            except Exception as e:
                self.read_try += 1

                if self.read_try == 1000:
                    msg = "Error, read data failed, detail:%s" % e
                    err_msg = {"type": -2,
                               "msg": msg}
                    logging.error(err_msg)
                    self.event.set()
                    raise TailError(traceback.format_exc())
                time.sleep(0.1)
            time.sleep(s)

    def stop(self):
        """ 停止tail文件
        """
        self.event.set()

    def register_callback(self, func):
        """ Overrides default callback function to provided function. """
        self.callback = func

    def check_file_validity(self, file_):
        """ Check whether the a given file exists, readable and is a file """
        if not os.access(file_, os.F_OK):
            raise TailError("File '%s' does not exist" % (file_))
        if not os.access(file_, os.R_OK):
            raise TailError("File '%s' not readable" % (file_))
        if os.path.isdir(file_):
            raise TailError("File '%s' is a directory" % (file_))


class TailError(Exception):

    """ Custom error type.
    """

    def __init__(self, msg):
        """ Init.
        """
        self.message = msg

    def __str__(self):
        """ str.
        """
        return self.message


if __name__ == '__main__':
    t = Tail("./acc.log")

    def print_msg(msg):
        print msg

    t.register_callback(print_msg)

    t.follow()

    print "hello"

""" vim: set ts=4 sw=4 sts=4 tw=100 et: """
