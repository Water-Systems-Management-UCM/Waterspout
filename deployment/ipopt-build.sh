mkdir /var/waterspout/coinbrew_build
cd /var/waterspout/coinbrew_build

LD_LIBRARY_PATH="/var/waterspout/coinbrew/ipopt:/var/waterspout/ipopt_dist/lib:/usr/lib/coinbrew/ipopt:/usr/lib/coinbrew/ipopt/lib:/usr/lib/x86_64-linux-gnu/"
PATH="$PATH:/var/waterspout/coinbrew/ipopt:/var/waterspout/ipopt_dist/bin:/usr/lib/coinbrew/ipopt:/usr/lib/coinbrew/ipopt/bin:/usr/lib/x86_64-linux-gnu/"
PKG_CONFIG_PATH="$PKG_CONFIG_PATH:/var/waterspout/coinbrew/ipopt:/var/waterspout/ipopt_dist/lib:/usr/lib/coinbrew/ipopt:/usr/lib/x86_64-linux-gnu/"

wget -O ./coinbrew https://raw.githubusercontent.com/coin-or/coinbrew/master/coinbrew
chmod u+x ./coinbrew
sudo ./coinbrew fetch Ipopt --no-prompt
sudo ./coinbrew build Ipopt --prefix=/var/waterspout/coinbrew/ipopt --test --no-prompt --verbosity=3
sudo ./coinbrew install Ipopt --no-prompt
sudo rm -fr ./build