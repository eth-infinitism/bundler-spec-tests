defaultVer=0.7
NAME=accountabstraction/testrunner
VER=${VER:-$defaultVer}
cd `dirname $0`
docker build -t $NAME:$VER .
echo docker push $NAME:$VER
