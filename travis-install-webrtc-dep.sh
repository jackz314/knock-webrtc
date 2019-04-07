#Depot tools
cd $HOME
mkdir webrtc-dep
cd webrtc-dep
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH=$PATH:$HOME/webrtc-dep/depot_tools

#gclient stuff
mv .gclient ../.gclient #move gclient to parent directory to use as config
sed -i -e "s|'src/resources'],|'src/resources'],'condition':'rtc_include_tests==true',|" DEPS # not get resources when gclient sync
mv `pwd` ../src #rename the current directory (repo root) to src so all the scripts work without problem
#not doing gclient sync directly here since doing it individually provides more insight and error log