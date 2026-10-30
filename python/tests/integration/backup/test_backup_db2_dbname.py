# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MASCORE-20519: backup pipeline must honour DB2_DBNAME.

The mas-backup pipeline previously had no way to pass a custom Db2 database
name (db2_dbname) to the mas-devops-db2 Tekton task, causing it to always
default to BLUDB regardless of the actual database name in the Db2 catalog.
"""

from mas.cli.backup.argParser import backupArgParser


def test_manage_db2_dbname_flag_accepted():
    """--manage-db2-dbname is accepted and stored in manage_db2_dbname.

    GIVEN a backup invocation with --backup-manage-db and --manage-db2-dbname MYDB
    WHEN the argument parser processes the arguments
    THEN manage_db2_dbname is set to MYDB
    """
    args = backupArgParser.parse_args(
        [
            "--instance-id",
            "inst1",
            "--backup-storage-class",
            "nfs-client",
            "--backup-storage-access-mode",
            "ReadWriteMany",
            "--backup-manage-db",
            "--manage-db2-namespace",
            "db2u",
            "--manage-db2-instance-name",
            "mas-inst1-masdev-manage",
            "--manage-db2-backup-type",
            "offline",
            "--manage-db2-dbname",
            "MYDB",
            "--no-confirm",
        ]
    )
    assert args.manage_db2_dbname == "MYDB"


def test_facilities_db2_dbname_flag_accepted():
    """--facilities-db2-dbname is accepted and stored in facilities_db2_dbname.

    GIVEN a backup invocation with --backup-facilities-db and --facilities-db2-dbname FACDB
    WHEN the argument parser processes the arguments
    THEN facilities_db2_dbname is set to FACDB
    """
    args = backupArgParser.parse_args(
        [
            "--instance-id",
            "inst1",
            "--backup-storage-class",
            "nfs-client",
            "--backup-storage-access-mode",
            "ReadWriteMany",
            "--backup-facilities-db",
            "--facilities-db2-namespace",
            "db2u",
            "--facilities-db2-instance-name",
            "mas-inst1-masdev-facilities",
            "--facilities-db2-backup-type",
            "offline",
            "--facilities-db2-dbname",
            "FACDB",
            "--no-confirm",
        ]
    )
    assert args.facilities_db2_dbname == "FACDB"


def test_manage_db2_dbname_defaults_to_none_when_not_provided():
    """manage_db2_dbname defaults to None when --manage-db2-dbname is omitted.

    GIVEN a backup invocation without --manage-db2-dbname
    WHEN the argument parser processes the arguments
    THEN manage_db2_dbname is None (not defaulted to BLUDB by the CLI)
    """
    args = backupArgParser.parse_args(
        [
            "--instance-id",
            "inst1",
            "--backup-storage-class",
            "nfs-client",
            "--backup-storage-access-mode",
            "ReadWriteMany",
            "--backup-manage-db",
            "--manage-db2-namespace",
            "db2u",
            "--manage-db2-instance-name",
            "mas-inst1-masdev-manage",
            "--manage-db2-backup-type",
            "offline",
            "--no-confirm",
        ]
    )
    assert args.manage_db2_dbname is None


def test_facilities_db2_dbname_defaults_to_none_when_not_provided():
    """facilities_db2_dbname defaults to None when --facilities-db2-dbname is omitted.

    GIVEN a backup invocation without --facilities-db2-dbname
    WHEN the argument parser processes the arguments
    THEN facilities_db2_dbname is None (not defaulted to BLUDB by the CLI)
    """
    args = backupArgParser.parse_args(
        [
            "--instance-id",
            "inst1",
            "--backup-storage-class",
            "nfs-client",
            "--backup-storage-access-mode",
            "ReadWriteMany",
            "--backup-facilities-db",
            "--facilities-db2-namespace",
            "db2u",
            "--facilities-db2-instance-name",
            "mas-inst1-masdev-facilities",
            "--facilities-db2-backup-type",
            "offline",
            "--no-confirm",
        ]
    )
    assert args.facilities_db2_dbname is None
