#!/bin/bash
#gclient stuff
mv .gclient ../.gclient #move gclient to parent directory to use as config
sed -i -e "s|'src/resources'],|'src/resources'],'condition':'rtc_include_tests==true',|" DEPS # not get resources when gclient sync
mv `pwd` ../src #rename the current directory (repo root) to src so all the scripts work without problem
echo "checking cached folders"
echo "$(du -h third_party)"
if test -f custom_cache/.gclient_entries; then
    echo "cached .gclient_entries exist, deploying it"
    mv custom_cache/.gclient_entries ../.gclient_entries
else
    echo "no cached .gclient_entries found"
fi
time gclient sync #takes quite a while
mv ../.gclient_entries custom_cache/.gclient_entries #store gclient_entries
chmod u+x tools_webrtc/android/build_aar.py
chmod u+x publish-maven.sh
./tools_webrtc/android/build_aar.py
if [ $? -eq 0 ]; then #publish to maven repo
    ./publish-maven.sh
else #abort
    echo "aborting publish to maven since build failed" 
fi