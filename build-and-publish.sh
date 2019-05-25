#!/bin/bash
chmod u+x tools_webrtc/android/build_aar.py
chmod u+x publish-maven.sh
./tools_webrtc/android/build_aar.py
[ $? -eq 0 ] && ./publish-maven.sh || echo "aborting publish to maven since build failed" #publish to maven repo