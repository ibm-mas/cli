#!/usr/bin/env python3

import sys

import mg.cluster
import mg.catalogs
import mg.subscriptions

if __name__ == "__main__":
    output_dir = sys.argv[1]

  mg.cluster.summarize(output_dir)
  mg.catalogs.summarize(output_dir)
  mg.subscriptions.summarize(output_dir)
