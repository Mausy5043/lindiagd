#! /bin/sh

# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > $HOME/.synodiagd.branch

if [ ! -e /mnt/share1 ]; then
  echo "Creating mountpoint..."
  sudo mkdir /mnt/share1
fi

#pushd doesnt work on busybox
cd $HOME/synodiagd
  ./00-scriptmanager.sh
#popd doesnt work on busybox
cd $HOME

exit 0
