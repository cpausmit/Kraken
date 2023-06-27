Install cvmfs on my fedora box

https://halldweb.jlab.org/wiki/index.php/HOWTO_Install_and_Use_the_CVMFS_Client


 sudo dnf install fuse-devel libcap-devel autofs uuid-devel sqlite-devel valgrind

 cd ~/local
 rm -rf cvmfs
 git clone https://github.com/cvmfs/cvmfs
 cd cvmfs
 git checkout cvmfs-2.8.1

 mkdir -p build
 cd build
 cmake ../


 make
 sudo make install

