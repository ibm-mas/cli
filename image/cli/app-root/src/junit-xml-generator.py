#!/usr/bin/env python3
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************
import argparse
import os
from junit_xml import TestSuite, TestCase

#
# The test-cases is a command seperated list of testcasename:timetaken
# Execute: 
#  `python junit-xml-generator.py --test-suite-name testsuite1 --test-cases operator-catalog:54,secret-update:9 --output-dir .`
# 
#
if __name__ == "__main__":
    # Initialize the properties we need
    parser = argparse.ArgumentParser()

    # Primary Options
    parser.add_argument("--test-suite-name", required=True)
    parser.add_argument("--test-cases", required=True)
    parser.add_argument("--output-dir", required=True)

    args, unknown = parser.parse_known_args()

    test_cases_dict = []
    test_case_list = args.test_cases.split(',')
    for test_case in test_case_list:
        test_case_name = test_case.split(':')[0]
        test_case_time = int(test_case.split(':')[1])
        print(f"Adding test_case: {test_case_name} with elapsed time {test_case_time}")
        test_cases_dict.append(TestCase(test_case_name, test_case_name, test_case_time))

    print(f"Creating testsuite : {args.test_suite_name}")
    ts = TestSuite(args.test_suite_name, test_cases_dict)

    with open(os.path.join(args.output_dir, 'output.xml'), 'w') as f:
        TestSuite.to_file(f, [ts], prettyprint=False)
