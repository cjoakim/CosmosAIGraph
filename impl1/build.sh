#!/bin/bash

# This is the unified build script for this application.  It can be used
# to deploy the common code, create the python virtual environments, and
# build the Docker images.
# Chris Joakim, Microsoft

for var in "$@"
    do
        case $var in
            help | --help)
                echo "Examples of using this common build script:"
                echo "  ./build.sh deploy               # deploys the common code in app_common"
                echo "  ./build.sh venv                 # recreates the python virtual environments"
                echo "  ./build.sh docker               # builds the Docker images"
                echo "  ./build.sh deploy venv docker   # executes all of the above in sequence"
                ;;
            deploy)
                cd app_common
                echo 'executing Apache Ant script to deploy common code ...'
                ant -f deploy_master_code.xml
                cd ..
                ;;
            venv)
                echo "creating python virtual environments ..."
                ./venv-builds.sh
                ;;
            docker)
                echo "executing docker image builds ..."
                ./docker-builds.sh
                ;;
        esac
done

echo ""
