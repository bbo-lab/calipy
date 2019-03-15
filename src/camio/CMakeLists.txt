# Build camera hardware input/output library
option(CAMIO_WITH_DUMMY "Build camio with dummy camera" ON)
option(CAMIO_WITH_PYLON "Build camio with pylon support" OFF)
option(CAMIO_WITH_APTINA "Build camio with aptina support" OFF)
option(CAMIO_WITH_PIXY "Build camio with pixy support" OFF)

# Find and setup Pylon
if(CAMIO_WITH_PYLON)
  find_package(Pylon5 REQUIRED)
endif()

# Find and setup aptina
if(CAMIO_WITH_APTINA)
  find_package(libaptina REQUIRED)
endif()

# Find and setup pixy
if(CAMIO_WITH_PIXY)
  find_package(libusb-1.0 REQUIRED)
  find_package(libpixyusb REQUIRED)
  include_directories(${LIBUSB_1_INCLUDE_DIRS})
endif()


### Source Files ###
set(CAMIO_SOURCE
  camio.cpp
  Frame.cpp
)

if(CAMIO_WITH_DUMMY)
  list(APPEND CAMIO_SOURCE
    dummy/DummyCamera.cpp
    dummy/DummyAdapter.cpp
  )
endif()

if(CAMIO_WITH_PYLON)
  list(APPEND CAMIO_SOURCE
    pylon/PylonFrame.cpp
    pylon/PylonCamera.cpp
    pylon/PylonAdapter.cpp
  )
endif()

if(CAMIO_WITH_APTINA)
  list(APPEND CAMIO_SOURCE
    aptina/AptinaFrame.cpp
    aptina/AptinaCamera.cpp
    aptina/AptinaAdapter.cpp
  )
endif()

if(CAMIO_WITH_PIXY)
  list(APPEND CAMIO_SOURCE
    pixy/PixyCamera.cpp
    pixy/PixyAdapter.cpp
  )
endif()


if(BUILD_AS_PYTHON_EXTENSION)
  pybind11_add_module(camio pycamio.cpp ${CAMIO_SOURCE})

  install(TARGETS camio DESTINATION multiview)
else()
  # Build C++ camera hardware input/output library
  add_library(camio ${CAMIO_SOURCE})

  install(TARGETS camio
          DESTINATION lib)

  # Build command line util
  add_executable (camctl camctl.cpp)
  target_link_libraries (camctl PRIVATE camio ${OpenCV_LIBRARIES})

  install(TARGETS camctl
          DESTINATION bin)
endif()


if(CAMIO_WITH_DUMMY)
  target_compile_definitions(camio PUBLIC "-DCAMIO_WITH_DUMMY")
endif()

if(CAMIO_WITH_PYLON)
  target_link_libraries(camio PRIVATE Pylon5::Base)
  target_compile_definitions(camio PUBLIC "-DCAMIO_WITH_PYLON")

  if(TARGET camctl)
	target_link_libraries(camctl PRIVATE Pylon5::Base Pylon5::Utility)
  endif()
endif()

if(CAMIO_WITH_APTINA)
  target_link_libraries(camio PRIVATE apbase)
  target_compile_definitions(camio PUBLIC "-DCAMIO_WITH_APTINA")
endif()

if(CAMIO_WITH_PIXY)
  target_link_libraries(camio PRIVATE pixyusb usb)
  target_compile_definitions(camio PUBLIC "-DCAMIO_WITH_PIXY")
endif()
