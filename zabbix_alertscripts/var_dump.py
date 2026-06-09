#!/usr/bin/env python3
import os
import sys
import logging
import logging.handlers


SCRIPT_FILE = os.path.basename(__file__)

### log出力設定　※rsyslogに渡す設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(logging.DEBUG)
HANDLER=logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6')
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d] %(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def main():
    LOGGER.info("")
    LOGGER.info("=== var_dump start ===")
    for index, arg in enumerate(sys.argv):
        log="{0}   {1}".format(index, arg)
        LOGGER.info(log)
        print(log)
    LOGGER.info("=== var_dump end ===")
    LOGGER.info("")


if __name__ == "__main__":
    main()
