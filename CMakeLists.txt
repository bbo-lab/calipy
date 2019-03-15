cmake_minimum_required(VERSION 3.1.0 FATAL_ERROR)

project(multiview VERSION 0.1.0 LANGUAGES C CXX)

# Set build mode
if(SKBUILD)
  set(BUILD_AS_PYTHON_EXTENSION ${SKBUILD})
else()
  set(BUILD_AS_PYTHON_EXTENSION FALSE)
endif()

# Generate git based version info
#find_package(Git QUIET)
#if(GIT_FOUND)
#  execute_process(COMMAND ${GIT_EXECUTABLE} describe --long --dirty=+
#                  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
#                  OUTPUT_VARIABLE PROJECT_GIT_VERSION)
#  string(STRIP ${PROJECT_GIT_VERSION} PROJECT_GIT_VERSION)
#else()
#  set(PROJECT_GIT_VERSION "v${PROJECT_VERSION}-unknown")
#endif()

set(CMAKE_CXX_STANDARD 14)


## CMake configuration ##
cmake_policy(SET CMP0057 NEW)
set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH}" "${CMAKE_SOURCE_DIR}/cmake")


## Dependencies ##

# Find and setup OpenCV
find_package(OpenCV 3 REQUIRED COMPONENTS core highgui)
#include_directories(${OpenCV_INCLUDE_DIRS})

if(BUILD_AS_PYTHON_EXTENSION)
  find_package(pybind11 REQUIRED)
endif()


## Libraries ##

add_subdirectory(src/camio)
