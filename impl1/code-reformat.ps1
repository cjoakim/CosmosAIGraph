
# This script reformats the python codebase per the formatting rules defined
# in the 'black' library.  This assists in stress-free team development with
# no code formatting debates.
# Chris Joakim, Microsoft

echo '===================='
echo 'app_ai ...'
cd app_ai
black *.py
black pysrc 
cd ..

echo '===================='
echo 'app_common ...'
cd app_common
black *.py
black pysrc 
cd ..

echo '===================='
echo 'app_console ...'
cd app_console
black *.py
black pysrc 
cd ..

echo '===================='
echo 'app_graph ...'
cd app_graph
black *.py
black pysrc 
cd ..

echo '===================='
echo 'app_web ...'
cd app_web
black *.py
black pysrc 
cd ..
