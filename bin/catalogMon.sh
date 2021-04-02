#!/bin/bash
book=$1
nFilesT2=`list /cms/store/user/paus/$book/*/tmp*|cut -d ' ' -f2 | wc -l`
nTodo=`grep $book /home/cmsprod/cms/work/fibs/checkFile.list |wc -l`

echo " FileT2: $nFilesT2 Todo: $nTodo "