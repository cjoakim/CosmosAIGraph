
# This script reformats the python codebase per the formatting rules defined
# in the 'black' library.  This assists in stress-free team development with
# no code formatting debates.
# Chris Joakim, Microsoft

echo '===================='
echo 'app_common (current dir)'
pwd
black *.py
black pysrc 

echo '===================='
echo 'app_console ...'
cd ..\app_console
pwd
black *.py
black pysrc 

echo '===================='
echo 'app_graph ...'
cd ..\app_graph
pwd
black *.py
black pysrc 


echo '===================='
echo 'app_web ...'
cd ..\app_web
pwd
black *.py
black pysrc

cd ..\app_common
