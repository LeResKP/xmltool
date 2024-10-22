#!/usr/bin/env python


def truncate(s, limit=30):
    limit += 1
    if len(s) > limit:
        s = s[:limit]
        for i in range(len(s), 0, -1):
            if s[i - 1] == " ":
                return s.rstrip() + "..."
            s = s[:-1]
    return s
