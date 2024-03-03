
# Build the several Python Virtual Environments (venv) for this app.
# Chris Joakim, Microsoft

cd .\app_ai\
pwd
echo 'building app_ai python virtual environment ...'
.\venv.ps1
cd ..

cd .\app_common\
pwd
echo 'building app_common python virtual environment ...'
.\venv.ps1
cd ..

cd .\app_console\
pwd
echo 'building app_console python virtual environment ...'
.\venv.ps1
cd ..

cd .\app_graph\
pwd
echo 'building app_graph python virtual environment ...'
.\venv.ps1
cd ..

cd .\app_web\
pwd
echo 'building app_web python virtual environment ...'
.\venv.ps1
cd ..
pwd

echo 'done'
