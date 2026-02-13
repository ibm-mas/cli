import pytest
import os

from mas.cli.install.app import InstallApp
from mas.cli.update.app import UpdateApp
from mas.cli.upgrade.app import UpgradeApp
from mas.cli.uninstall.app import UninstallApp
from mas.cli import __version__ as package_version

from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def test_package_version_matches_expected():
    """
    Test that the package version (__version__ in __init__.py) matches the expected version.
    
    During CI builds, the VERSION_NOPREREL environment variable is set and the version
    in __init__.py is updated via sed. This test ensures that the sed command worked
    correctly and the version was properly set.
    """
    expected_version = os.environ.get('VERSION_NOPREREL')
    
    if expected_version:
        # In CI environment, verify the version matches what was set
        assert package_version == expected_version, (
            f"Package version mismatch: expected '{expected_version}' "
            f"but got '{package_version}'. The sed command in the build workflow "
            f"may have failed to update python/src/mas/cli/__init__.py"
        )
    else:
        # In local development, just verify it's the default placeholder
        assert package_version == "100.0.0", (
            f"Package version should be '100.0.0' in development, "
            f"but got '{package_version}'"
        )


def test_cli_version_matches_expected():
    """
    Test that the CLI version (self.version in cli.py) matches the expected version.
    
    During CI builds, the VERSION environment variable is set and the version
    in cli.py is updated via sed. This test ensures that the sed command worked
    correctly and the version was properly set.
    """
    expected_version = os.environ.get('VERSION')
    
    with create_app_session(output=DummyOutput()):
        # Test with InstallApp as a representative of BaseApp
        app = InstallApp()
        
        if expected_version:
            # In CI environment, verify the version matches what was set
            assert app.version == expected_version, (
                f"CLI version mismatch: expected '{expected_version}' "
                f"but got '{app.version}'. The sed command in the build workflow "
                f"may have failed to update python/src/mas/cli/cli.py"
            )
        else:
            # In local development, just verify it's the default placeholder
            assert app.version == "100.0.0-pre.local", (
                f"CLI version should be '100.0.0-pre.local' in development, "
                f"but got '{app.version}'"
            )


def test_all_apps_have_consistent_version():
    """
    Test that all CLI apps (Install, Update, Upgrade, Uninstall) report the same version.
    
    This ensures consistency across all command implementations.
    """
    with create_app_session(output=DummyOutput()):
        install_app = InstallApp()
        update_app = UpdateApp()
        upgrade_app = UpgradeApp()
        uninstall_app = UninstallApp()
        
        versions = {
            'InstallApp': install_app.version,
            'UpdateApp': update_app.version,
            'UpgradeApp': upgrade_app.version,
            'UninstallApp': uninstall_app.version
        }
        
        # All versions should be identical
        unique_versions = set(versions.values())
        assert len(unique_versions) == 1, (
            f"Version mismatch across apps: {versions}. "
            f"All apps should report the same version."
        )

# Made with Bob
