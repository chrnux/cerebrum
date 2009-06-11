#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from ceresync import sync
from ceresync import config

config.parse_args()

def main():
    s= sync.Sync(incr=False)
    print s.cmd.get_last_changelog_id() 
    s.close()

if __name__ == "__main__":
    main()

