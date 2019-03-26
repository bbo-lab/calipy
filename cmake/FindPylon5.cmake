#.rst:
# FindPylon5
# -------
#
# Finds the Basler Pylon library version 5 and related files.
#
# This will define the following variables::
#
#   Pylon5_FOUND    - True if the system has the Foo library
#   Pylon5_VERSION  - The version of the Foo library which was found
#
# and the following imported targets::
#
#   Pylon5::Base        - pylon base libraries
#   Pylon5::C           - pylon C libraries
#   Pylon5::Utility     - pylon Utility  libraries
#   Pylon5::TL::USB     - pylon USB transport layer libraries
#   Pylon5::TL::GigE    - pylon GigE transport layer libraries
#   Pylon5::TL::CamEmu  - pylon CamEmu transport layer libraries
#   Pylon5::TL::BCON    - pylon BCON transport layer libraries
#   Pylon5::TL::GTC     - pylon GTC transport layer libraries
#
#   And a few more, see source code.

# Finds a library and defines it as imported target
function(find_and_define_library _TARGET _NAMES _PATHS _INCLUDES _DEPENDENCIES)
  string(REPLACE "::" "_" TARGET_LIB_VAR_NAME "${_TARGET}_LIBRARY")

  find_library(${TARGET_LIB_VAR_NAME}
    NAMES ${_NAMES}
    PATHS ${_PATHS}
  )

  # If library is found
  if(${TARGET_LIB_VAR_NAME})
    # Create imported target with location
    add_library(${_TARGET} UNKNOWN IMPORTED)
    set_target_properties(${_TARGET} PROPERTIES
      IMPORTED_LOCATION "${${TARGET_LIB_VAR_NAME}}"
    )

    # If include is supplied, set it
    if(_INCLUDES)
      set_target_properties(${_TARGET} PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${_INCLUDES}"
      )
    endif()

    # If an interface dependency is supplied, set it
    if(_DEPENDENCIES)
      set_target_properties(${_TARGET} PROPERTIES
        INTERFACE_LINK_LIBRARIES "${_DEPENDENCIES}"
      )
    endif()
  endif()
endfunction(find_and_define_library)

# Determin include path
find_path(Pylon5_INCLUDE_DIR
  NAMES GenICam.h GenICamVersion.h
  PATHS /opt/pylon5/include
  	"$ENV{PYLON_DEV_DIR}/include"
	${CMAKE_INCLUDE_PATH}
)

# Determin version from header
if(Pylon5_INCLUDE_DIR)
    file(STRINGS "${Pylon5_INCLUDE_DIR}/pylon/PylonVersionNumber.h"
          PYLON_VERSION_FROM_HEADER REGEX "^[ \t]*#define[
    \t]+PYLON_VERSION_[A-Z]+[ \t]+[0-9]+.*$")

    if(PYLON_VERSION_FROM_HEADER)
        foreach(item IN ITEMS MAJOR MINOR SUBMINOR)
           string(REGEX REPLACE ".*#define[ \t]+PYLON_VERSION_${item}[
    \t]+([0-9]+).*"
                  "\\1" TEMP ${PYLON_VERSION_FROM_HEADER})
           set("PYLON_VERSION_${item}" ${TEMP} CACHE STRING "Version number of Pylon")
        endforeach()
        set(PYLON_VERSION_PATCH ${PYLON_VERSION_SUBMINOR})
        set(Pylon5_VERSION "${PYLON_VERSION_MAJOR}.${PYLON_VERSION_MINOR}.${PYLON_VERSION_PATCH}")
    endif()
endif()


# Set library search location
set(PYLON_LIBRARY_PATHS
  /opt/pylon5/lib64
  /opt/pylon5/lib32
  "$ENV{PYLON_DEV_DIR}/lib/x64"
  "$ENV{PYLON_DEV_DIR}/lib/Win32"
  ${Pylon5_INCLUDE_DIR}/../lib
)

# Little wrapper to avoid repeating pylon specific arguments, all extra args are understood as dependency
function(find_and_define_pylon_library _TARGET _NAME)
  foreach(DEPENDECY IN ITEMS ${ARGN})
    list(APPEND DEPENDECIES "Pylon5::${DEPENDECY}")
  endforeach()
  find_and_define_library("Pylon5::${_TARGET}" ${_NAME} "${PYLON_LIBRARY_PATHS}" "${Pylon5_INCLUDE_DIR}" "${DEPENDECIES}")
endfunction(find_and_define_pylon_library)

# Support libraries
if(MSVC)
  set(PYLON_SUPPORT_VERSION_SUFFIX "MD_VC141_v3_1_Basler_pylon_v5_1")
  set(PYLON_BASE_VERSION_SUFFIX "_v5_1")
else()
  set(PYLON_SUPPORT_VERSION_SUFFIX "_gcc_v3_1_Basler_pylon_v5_1")
  set(PYLON_BASE_VERSION_SUFFIX "")
endif()

find_and_define_pylon_library(Support::GCBase GCBase${PYLON_SUPPORT_VERSION_SUFFIX})

if(MSVC)

  find_and_define_pylon_library(Support::GenApi GenApi${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase)

else()

  find_and_define_pylon_library(Support::MathParser MathParser${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase)

  find_and_define_pylon_library(Support::XmlParser XmlParser${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase)

  find_and_define_pylon_library(Support::NodeMapData NodeMapData${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase)

  find_and_define_pylon_library(Support::Log Log${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase)

  find_and_define_pylon_library(Support::GenApi GenApi${PYLON_SUPPORT_VERSION_SUFFIX} Support::GCBase
                                                                                      Support::MathParser
                                                                                      Support::XmlParser
										      Support::NodeMapData
										      Support::Log)
endif()



# Base librariea
find_and_define_pylon_library(Base pylonbase${PYLON_BASE_VERSION_SUFFIX} Support::GenApi)

find_and_define_pylon_library(Utility pylonutility${PYLON_BASE_VERSION_SUFFIX} Base)

find_and_define_pylon_library(C pylonc${PYLON_BASE_VERSION_SUFFIX} Utility)


# Transport layer libraries
find_and_define_pylon_library(TL::GTC pylon_TL_gtc Base)

find_and_define_pylon_library(TL::CamEmu pylon_TL_camemu Utility)

find_and_define_pylon_library(TL::BXApi bxapi)
find_and_define_pylon_library(TL::BCON pylon_TL_bcon Base TL::BXApi)

find_and_define_pylon_library(TL::GXApi gxapi)
find_and_define_pylon_library(TL::GigE pylon_TL_gige Base TL::GXApi)

find_and_define_pylon_library(TL::UXApi uxapi)
find_and_define_pylon_library(TL::USB pylon_TL_usb Base TL::UXApi)

# Set all the requred variables
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Pylon5
  FOUND_VAR Pylon5_FOUND
  REQUIRED_VARS
    Pylon5_Base_LIBRARY
    Pylon5_C_LIBRARY
    Pylon5_Utility_LIBRARY
#    Pylon5_TL_GTC_LIBRARY
#    Pylon5_TL_CamEmu_LIBRARY
#    Pylon5_TL_BXApi_LIBRARY
#    Pylon5_TL_BCON_LIBRARY
#    Pylon5_TL_GXApi_LIBRARY
#    Pylon5_TL_GigE_LIBRARY
#    Pylon5_TL_UXApi_LIBRARY
#    Pylon5_TL_USB_LIBRARY
    Pylon5_Support_GCBase_LIBRARY
#    Pylon5_Support_MathParser_LIBRARY
#    Pylon5_Support_XmlParser_LIBRARY
#    Pylon5_Support_NodeMapData_LIBRARY
#    Pylon5_Support_Log_LIBRARY
    Pylon5_Support_GenApi_LIBRARY
    Pylon5_INCLUDE_DIR
  VERSION_VAR Pylon5_VERSION
)
