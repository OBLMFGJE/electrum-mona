#!/bin/bash

# You probably need to update only this link
ELECTRUM_GIT_URL=git://github.com/wakiyamap/electrum-mona.git
BRANCH=master
NAME_ROOT=electrum-mona
PYTHON_VERSION=3.6.3

if [ "$#" -gt 0 ]; then
    BRANCH="$1"
fi

# These settings probably don't need any change
export WINEPREFIX=/opt/wine64
#export PYTHONHASHSEED=22


PYHOME=c:/python$PYTHON_VERSION
PYTHON="wine $PYHOME/python.exe -OO -B"


# Let's begin!
cd `dirname $0`
set -e

cd tmp

if [ -d "electrum-mona-git" ]; then
    # GIT repository found, update it
    echo "Pull"
    cd electrum-mona-git
    git checkout $BRANCH
    git pull
    cd ..
else
    # GIT repository not found, clone it
    echo "Clone"
    git clone -b $BRANCH $ELECTRUM_GIT_URL electrum-mona-git
fi

cd electrum-mona-git
VERSION=`git describe --tags`
echo "Last commit: $VERSION"

cd ..

rm -rf $WINEPREFIX/drive_c/electrum-mona
cp -r electrum-mona-git $WINEPREFIX/drive_c/electrum-mona
cp electrum-mona-git/LICENCE .

# add locale dir
cp -r ../../../lib/locale $WINEPREFIX/drive_c/electrum-mona/lib/

# Build Qt resources
wine $WINEPREFIX/drive_c/python$PYTHON_VERSION/Scripts/pyrcc5.exe C:/electrum-mona/icons.qrc -o C:/electrum-mona/gui/qt/icons_rc.py


pushd $WINEPREFIX/drive_c/electrum-mona
$PYTHON setup.py install
popd

# Build target
pushd $WINEPREFIX/drive_c/electrum-mona/lib
$PYTHON setup.py build_ext --inplace
popd


cd ..

rm -rf dist/

# build standalone version
wine "C:/python$PYTHON_VERSION/scripts/pyinstaller.exe" --noconfirm --ascii --name $NAME_ROOT-$VERSION.exe -w deterministic.spec 

# build NSIS installer
# $VERSION could be passed to the electrum.nsi script, but this would require some rewriting in the script iself.
if [ -d "$WINEPREFIX/drive_c/Program Files (x86)" ]; then
    wine "$WINEPREFIX/drive_c/Program Files (x86)/NSIS/makensis.exe" /DPRODUCT_VERSION=$VERSION electrum.nsi
else
    wine "$WINEPREFIX/drive_c/Program Files/NSIS/makensis.exe" /DPRODUCT_VERSION=$VERSION electrum.nsi
fi

cd dist
mv electrum-mona-setup.exe $NAME_ROOT-$VERSION-setup.exe
cd ..

# build portable version
cp portable.patch $WINEPREFIX/drive_c/electrum-mona
pushd $WINEPREFIX/drive_c/electrum-mona
patch < portable.patch 
popd

wine "C:/python$PYTHON_VERSION/scripts/pyinstaller.exe" --noconfirm --ascii --name $NAME_ROOT-$VERSION-portable.exe -w deterministic.spec

echo "Done."
