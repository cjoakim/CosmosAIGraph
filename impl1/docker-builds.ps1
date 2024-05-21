# Build the two microservice Docker images for this app.
# Note: be sure to have Docker Desktop running on your system.
# Chris Joakim, Microsoft

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
