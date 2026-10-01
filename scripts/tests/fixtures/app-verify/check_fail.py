#!/usr/bin/env python3
"""Fixture check that always fails, for the fail recipe."""

import sys

print("check_fail: this check always fails", file=sys.stderr)
sys.exit(1)
