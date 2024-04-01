# Build the three microservice Docker images for this app.
# Chris Joakim, Microsoft

cd .\app_common\
echo 'executing Ant script to deploy common code ...'
ant -f deploy_master_code.xml
cd ..

cd .\app_graph\
pwd
echo 'building caig_graph image ...'
docker build -t cjoakim/caig_graph .
cd ..

cd .\app_web\
pwd
echo 'building caig_web image ...'
docker build -t cjoakim/caig_web .
cd ..
pwd

echo 'list of the local caig images:'
docker image ls | grep caig

echo 'next steps:'
echo '  docker push cjoakim/caig_graph:latest'
echo '  docker push cjoakim/caig_web:latest'

echo 'done'
