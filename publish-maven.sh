# used to publish aar to Maven repo hosted on github, run from root directory, make sure $GITHUB_TOKEN is available
buildNum=$(./get-build-num.sh)
echo "Publishing under build 1.0.$buildNum"
mkdir maven
cd maven
git clone https://$GITHUB_TOKEN@github.com/jackz314/jackz314-maven.git
cd jackz314-maven
git config --local user.name "Jack Zhang"
git config --local user.email "zhangmengyu10@gmail.com"
git checkout knock-webrtc
mvn org.apache.maven.plugins:maven-install-plugin:3.0.0-M1:install-file -DgroupId=com.jackz314 -DartifactId=knock-webrtc -Dversion=1.0.$buildNum -DlocalRepositoryPath=./ -Dpackaging=aar -Dfile=../../lib-knock-webrtc.aar -DgeneratePom=true -DcreateChecksum=true
git add -A #stage changes
git commit -m "Released knock-webrtc version 1.0.$buildNum"
git push