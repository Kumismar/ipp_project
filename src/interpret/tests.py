import unittest
import sys

import support.supportFunctions as supportFunctions
import support.errors as errors

import interpret

class SimpleUnitTest(unittest.TestCase):
    
    def test_exit():
        args = ["./interpret.py", "--random=argument", "--random=argument2"]

        with unittest.raises(SystemExit) as pytest_wrapped_e:
            interpret.parseArguments(args)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == errors.INVALID_CMDLINE_ARGS
                