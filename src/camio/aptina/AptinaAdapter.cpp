#include "AptinaAdapter.hpp"

#include <apbase.h>

#include <iostream>

#include "AptinaCamera.hpp"

namespace camio {
  std::string AptinaAdapter::version() {
    return std::string("libaptina v") + ap_Version();
  }


  AptinaAdapter::AptinaAdapter() {}

  AptinaAdapter::~AptinaAdapter() {
    ap_Finalize();
  }

  std::vector<CameraInfo> AptinaAdapter::enumerate() {
    ap_DeviceProbe(NULL);

    std::vector<CameraInfo> devices;

    for(int i = 0; i < ap_NumCameras(); i++) {
      AP_HANDLE handle = ap_Create(i);

      CameraInfo info;

      // Get name
      info.name = ap_GetPartNumber(handle);

      // Get id
      int length = ap_GetFuseID(handle, 0, 0, 0);
      char id[length];
      if(ap_GetFuseID(handle, 0, id, length) != length) {
        std::cerr << "Error getting fuse id." << std::endl;
      }

      info.id = id;
      // Add chip version here

      devices.push_back(info);

      ap_Destroy(handle);
    }

    return devices;
  }

  Camera* AptinaAdapter::open(std::string id) {

    auto devices = enumerate();

    int index = -1;
    for(int i = 0; i < devices.size(); i++) {
      if(devices[i].id == id) {
        index = i;
        break;
      }
    }

    if(index != -1)
      return new AptinaCamera(ap_Create(index));

    return nullptr;
  }

}
