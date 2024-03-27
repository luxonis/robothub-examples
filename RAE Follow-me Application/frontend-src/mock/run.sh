docker build -t rae-app-ros-be-mock .
docker run -it -v `pwd`:/project --network host rae-app-ros-be-mock
