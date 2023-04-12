import pytest

import interpret as ip
import errors

def test_RandomArguments_Exit():
    args = ["./interpret.py", "--random=argument", "--random=argument2"]

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        ip.parseArguments(args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == errors.INVALID_CMDLINE_ARGS
            