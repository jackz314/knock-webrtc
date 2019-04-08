#!/usr/bin/env python

# Copyright (c) 2017 The WebRTC project authors. All Rights Reserved.
#
# Use of this source code is governed by a BSD-style license
# that can be found in the LICENSE file in the root of the source
# tree. An additional intellectual property rights grant can be found
# in the file PATENTS.  All contributing project authors may
# be found in the AUTHORS file in the root of the source tree.

"""Script for publishing the built WebRTC AAR on Maven repository
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CHECKOUT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir))

sys.path.append(os.path.join(CHECKOUT_ROOT, 'third_party'))
import requests
import jinja2

sys.path.append(os.path.join(CHECKOUT_ROOT, 'tools_webrtc'))
from android.build_aar import BuildAar


ARCHS = ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64']
MAVEN_REPOSITORY = 'https://google.bintray.com/webrtc'
API = 'https://api.bintray.com'
PACKAGE_PATH = 'google/webrtc/google-webrtc'
CONTENT_API = API + '/content/' + PACKAGE_PATH
PACKAGES_API = API + '/packages/' + PACKAGE_PATH
GROUP_ID = 'com/jackz314'
ARTIFACT_ID = 'knock-webrtc'
COMMIT_POSITION_REGEX = r'^Cr-Commit-Position: refs/heads/master@{#(\d+)}$'
API_TIMEOUT_SECONDS = 10.0
UPLOAD_TRIES = 3
# The sleep time is increased exponentially.
UPLOAD_RETRY_BASE_SLEEP_SECONDS = 2.0
GRADLEW_BIN = os.path.join(CHECKOUT_ROOT,
                           'examples/androidtests/third_party/gradle/gradlew')
ADB_BIN = os.path.join(CHECKOUT_ROOT,
                       'third_party/android_sdk/public/platform-tools/adb')
AAR_PROJECT_DIR = os.path.join(CHECKOUT_ROOT, 'examples/aarproject')
AAR_PROJECT_GRADLE = os.path.join(AAR_PROJECT_DIR, 'build.gradle')
AAR_PROJECT_APP_GRADLE = os.path.join(AAR_PROJECT_DIR, 'app', 'build.gradle')
AAR_PROJECT_DEPENDENCY = "implementation 'org.webrtc:google-webrtc:1.0.+'"
AAR_PROJECT_VERSION_DEPENDENCY = "implementation 'org.webrtc:google-webrtc:%s'"

def _ParseArgs():
  parser = argparse.ArgumentParser(description='Releases WebRTC on Maven repo')
  parser.add_argument('--use-goma', action='store_true', default=False,
      help='Use goma.')
  parser.add_argument('--skip-tests', action='store_true', default=False,
      help='Skips running the tests.')
  parser.add_argument('--publish', action='store_true', default=False,
      help='Automatically publishes the library if the tests pass.')
  parser.add_argument('--build-dir', default=None,
      help='Temporary directory to store the build files. If not specified, '
           'a new directory will be created.')
  parser.add_argument('--aar-file', default=None,
      help='AAR file location, if not specified, will extract from root directory with name lib-knock-webrtc.aar')
  parser.add_argument('--verbose', action='store_true', default=False,
      help='Debug logging.')
  return parser.parse_args()

def _GetCommitVer():
  commit_ver = subprocess.check_output(
    ['git', 'describe', '--tags', '--abbrev=0', '--always'], cwd=CHECKOUT_ROOT).strip()
  return commit_ver

def _GetCommitHash():
  commit_hash = subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT_ROOT).strip()
  return commit_hash

def _GeneratePom(target_file, version, commit):
  env = jinja2.Environment(
    loader=jinja2.PackageLoader('release_aar'),
  )
  template = env.get_template('pom.jinja')
  pom = template.render(version=version, commit=commit)
  with open(target_file, 'w') as fh:
    fh.write(pom)


def _TestAAR(tmp_dir, username, password, version):
  """Runs AppRTCMobile tests using the AAR. Returns true if the tests pass."""
  logging.info('Testing library.')
  env = jinja2.Environment(
    loader=jinja2.PackageLoader('release_aar'),
  )

  gradle_backup = os.path.join(tmp_dir, 'build.gradle.backup')
  app_gradle_backup = os.path.join(tmp_dir, 'app-build.gradle.backup')

  # Make backup copies of the project files before modifying them.
  shutil.copy2(AAR_PROJECT_GRADLE, gradle_backup)
  shutil.copy2(AAR_PROJECT_APP_GRADLE, app_gradle_backup)

  try:
    maven_repository_template = env.get_template('maven-repository.jinja')
    maven_repository = maven_repository_template.render(
        url=MAVEN_REPOSITORY, username=username, password=password)

    # Append Maven repository to build file to download unpublished files.
    with open(AAR_PROJECT_GRADLE, 'a') as gradle_file:
      gradle_file.write(maven_repository)

    # Read app build file.
    with open(AAR_PROJECT_APP_GRADLE, 'r') as gradle_app_file:
      gradle_app = gradle_app_file.read()

    if AAR_PROJECT_DEPENDENCY not in gradle_app:
      raise Exception(
          '%s not found in the build file.' % AAR_PROJECT_DEPENDENCY)
    # Set version to the version to be tested.
    target_dependency = AAR_PROJECT_VERSION_DEPENDENCY % version
    gradle_app = gradle_app.replace(AAR_PROJECT_DEPENDENCY, target_dependency)

    # Write back.
    with open(AAR_PROJECT_APP_GRADLE, 'w') as gradle_app_file:
      gradle_app_file.write(gradle_app)

    # Uninstall any existing version of AppRTCMobile.
    logging.info('Uninstalling previous AppRTCMobile versions. It is okay for '
                 'these commands to fail if AppRTCMobile is not installed.')
    subprocess.call([ADB_BIN, 'uninstall', 'org.appspot.apprtc'])
    subprocess.call([ADB_BIN, 'uninstall', 'org.appspot.apprtc.test'])

    # Run tests.
    try:
      # First clean the project.
      subprocess.check_call([GRADLEW_BIN, 'clean'], cwd=AAR_PROJECT_DIR)
      # Then run the tests.
      subprocess.check_call([GRADLEW_BIN, 'connectedDebugAndroidTest'],
                            cwd=AAR_PROJECT_DIR)
    except subprocess.CalledProcessError:
      logging.exception('Test failure.')
      return False  # Clean or tests failed

    return True  # Tests pass
  finally:
    # Restore backups.
    shutil.copy2(gradle_backup, AAR_PROJECT_GRADLE)
    shutil.copy2(app_gradle_backup, AAR_PROJECT_APP_GRADLE)

def ReleaseAar(use_goma, skip_tests, publish, build_dir, aar_file):
  version = _GetCommitVer()
  commit = _GetCommitHash()
  logging.info('Releasing AAR version %s with hash %s', version, commit)

  # If build directory is not specified, create a temporary directory.
  use_tmp_dir = not build_dir
  if use_tmp_dir:
    build_dir = tempfile.mkdtemp()
  try:
    if not aar_file:
      aar_file = CHECKOUT_ROOT + 'lib-knock-webrtc.aar' #default
    base_name = ARTIFACT_ID + '-' + version
    third_party_licenses_file = os.path.join(build_dir, 'LICENSE.md')
    pom_file = os.path.join(build_dir, base_name + '.pom')

    logging.info('Preparing release at %s', build_dir)
    
    _GeneratePom(pom_file, version, commit)

    tests_pass = skip_tests or _TestAAR(build_dir, user, api_key, version)
    if not tests_pass:
      logging.info('Discarding library.')
      raise Exception('Test failure. Discarded library.')

    if publish:
      logging.info('Publishing library.')
    else:
      logging.info('Note: The library has not not been published automatically.'
                   ' Please do so manually if desired.')
  finally:
    if use_tmp_dir: #remove the temp folder if one is created
      shutil.rmtree(build_dir, True)


def main():
  args = _ParseArgs()
  logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
  ReleaseAar(args.use_goma, args.skip_tests, args.publish, args.build_dir, args.aar_file)


if __name__ == '__main__':
  sys.exit(main())
