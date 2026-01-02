import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

from tufup.client import Client

from myapp import settings

logger = logging.getLogger(__name__)

__version__ = settings.APP_VERSION


def progress_hook(bytes_downloaded: int, bytes_expected: int):
    progress_percent = bytes_downloaded / bytes_expected * 100
    print(f'\r{progress_percent:.1f}%', end='')
    time.sleep(0.2)
    if progress_percent >= 100:
        print('')


def update(pre: str, skip_confirmation: bool = False):
    # Create update client
    client = Client(
        app_name=settings.APP_NAME,
        app_install_dir=settings.INSTALL_DIR,
        current_version=settings.APP_VERSION,
        metadata_dir=settings.METADATA_DIR,
        metadata_base_url=settings.METADATA_BASE_URL,
        target_dir=settings.TARGET_DIR,
        target_base_url=settings.TARGET_BASE_URL,
        refresh_required=False,
    )

    # Perform update check
    new_update = client.check_for_updates(pre=pre)
    if new_update:
        # [optional] use custom metadata, if available
        if new_update.custom:
            print('changes in this update:')
            for item in new_update.custom.get('changes', []):
                print(f'\t- {item}')
        
        print(f'\nNew update available: {new_update}')
        
        # Download the update archive ourselves using tufup's internal method
        print('Downloading update...')
        
        # client._download_updates handles the download properly
        if progress_hook:
            client._fetcher.attach_progress_hook(
                hook=progress_hook, 
                bytes_expected=client.new_archive_info.length
            )
        
        # Download to the target directory
        target_path_str = client.download_target(targetinfo=client.new_archive_info)
        target_path = pathlib.Path(target_path_str)
        
        print(f'\nDownloaded to: {target_path}')
        
        # Extract to temp directory
        # Use a simpler temp path to avoid 8.3 short name issues on Windows
        import tarfile
        import ctypes
        
        # Get the long path name for temp directory
        temp_base = pathlib.Path(os.environ.get('TEMP', tempfile.gettempdir()))
        # Create our own subfolder with a simple name
        temp_extract_dir = temp_base / 'tufup_update'
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        temp_extract_dir.mkdir(parents=True)
        
        # Resolve to get long path name
        temp_extract_dir = temp_extract_dir.resolve()
        print(f'Extracting to: {temp_extract_dir}')
        
        with tarfile.open(target_path, 'r:gz') as tar:
            tar.extractall(temp_extract_dir)
        
        # Find the actual app directory (main.exe location)
        app_files = list(temp_extract_dir.rglob('main.exe'))
        if app_files:
            exe_parent = app_files[0].parent
            # If main.exe is next to _internal, use that directory
            actual_extract_dir = exe_parent
        else:
            # Fallback: use first subdirectory or temp dir itself
            dirs = [d for d in temp_extract_dir.iterdir() if d.is_dir()]
            actual_extract_dir = dirs[0] if dirs else temp_extract_dir
        
        print(f'App files in: {actual_extract_dir}')
        
        # For batch file compatibility, use environment variable paths
        # Copy files to a simple temp path
        simple_temp = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Temp' / 'upd'
        if simple_temp.exists():
            shutil.rmtree(simple_temp)
        
        # Copy files to simple path
        print('Preparing update files...')
        shutil.copytree(actual_extract_dir, simple_temp)
        
        # Use environment variables in batch - CMD handles them correctly
        src_dir = '%LOCALAPPDATA%\\Temp\\upd'
        dst_dir = '%LOCALAPPDATA%\\Programs\\my_app'
        temp_dir = '%LOCALAPPDATA%\\Temp\\upd'
        
        # Create batch script to install after app closes
        print('\n' + '='*60)
        print('Update downloaded and extracted.')
        print('The application will close to allow file replacement.')
        print('Please wait 10-15 seconds, then run the application again.')
        print('='*60 + '\n')
        
        # Batch script with delay to ensure main.exe is released
        batch_script = f'''@echo off
echo Waiting for application to close...
ping -n 6 127.0.0.1 >nul
echo Starting file copy...
xcopy "{src_dir}\\*.*" "{dst_dir}\\" /E /Y /I /H /R
if errorlevel 1 (
    echo Update failed with error.
) else (
    echo Update installed successfully.
)
echo Cleaning up...
rd /s /q "{temp_dir}" 2>nul
echo Done. Press any key to close...
pause
'''
        
        # Write batch file to LOCALAPPDATA (no Unicode in path)
        batch_path = os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'upd_install.bat')
        with open(batch_path, 'w', encoding='ascii') as f:
            f.write(batch_script)
        
        print(f'Starting install script: {batch_path}')
        
        # Clean up original temp dir (the one with Unicode path)
        try:
            shutil.rmtree(temp_extract_dir)
        except:
            pass
        
        # Start batch script in a visible console so user can see progress
        subprocess.Popen(
            f'start "" "{batch_path}"',
            shell=True
        )
        
        # Give a moment for the script to start, then exit
        sys.stdout.flush()
        time.sleep(2)
        print('Exiting application for update...')
        sys.exit(0)


def main(cmd_args):
    # a proper app would use argparse, but we just do minimal argument
    # parsing to keep things simple
    pre_release_channel = None
    skip_confirmation = False
    while cmd_args:
        arg = cmd_args.pop(0)
        if arg in ['a', 'b', 'rc']:
            pre_release_channel = arg
        else:
            skip_confirmation = arg == 'skip'

    # The app must ensure dirs exist
    for dir_path in [settings.INSTALL_DIR, settings.METADATA_DIR, settings.TARGET_DIR]:
        dir_path.mkdir(exist_ok=True, parents=True)

    # The app must be shipped with a trusted "root.json" metadata file,
    # which is created using the tufup.repo tools. The app must ensure
    # this file can be found in the specified metadata_dir. The root metadata
    # file lists all trusted keys and TUF roles.
    if not settings.TRUSTED_ROOT_DST.exists():
        shutil.copy(src=settings.TRUSTED_ROOT_SRC, dst=settings.TRUSTED_ROOT_DST)
        logger.info('Trusted root metadata copied to cache.')

    # Download and apply any available updates
    update(pre=pre_release_channel, skip_confirmation=skip_confirmation)

    # Do what the app is supposed to do
    print(f'Starting {settings.APP_NAME} {settings.APP_VERSION}...')
    ...
    print('Doing what the app is supposed to do...')
    print('Im in the version 9.0, the latest version')
    ...
    print('Done.')
