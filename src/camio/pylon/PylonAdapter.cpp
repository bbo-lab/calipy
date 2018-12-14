#include "PylonAdapter.hpp"

#include "PylonCamera.hpp"

#include <pylon/usb/BaslerUsbCamera.h>

namespace camio {

  std::string PylonAdapter::version() {
    return std::string("libpylon v") + Pylon::VersionInfo::getVersionString();
  }

  PylonAdapter::PylonAdapter(){
    Pylon::PylonInitialize();
  }

  PylonAdapter::~PylonAdapter(){
    Pylon::PylonTerminate();
  }

  std::vector<CameraInfo> PylonAdapter::enumerate() {
    // Get list of devices from library
    Pylon::DeviceInfoList devices;
    try {
      Pylon::CTlFactory& factory = Pylon::CTlFactory::GetInstance();

      /// ToDo: Remove this again as soon as GE is supported
      Pylon::ITransportLayer* tl
        = factory.CreateTl(Pylon::CBaslerUsbCamera::DeviceClass());

      tl->EnumerateDevices(devices);
      factory.ReleaseTl(tl);
      //factory.EnumerateDevices(devices);
    } catch(const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
    }

    // Repack and return result
    std::vector<CameraInfo> result;
    for(int i = 0; i < devices.size(); i++) {
      CameraInfo info;

      info.id = devices[i].GetSerialNumber();
      info.name = devices[i].GetModelName();
      info.description = devices[i].GetUserDefinedName() + " via " + devices[i].GetDeviceClass();

      result.push_back(info);
    }
    return result;
  }

  Camera* PylonAdapter::open(std::string id) {
    try {
      Pylon::CTlFactory& factory = Pylon::CTlFactory::GetInstance();

      // Select correct device using serial number
      Pylon::CDeviceInfo info;
      info.SetSerialNumber(id.c_str());
      info.SetDeviceClass(Pylon::CBaslerUsbCamera::DeviceClass()); /// ToDo: Fix and remove

      Pylon::IPylonDevice* device = factory.CreateDevice(info);

      return new PylonCamera(device);

    } catch(const Pylon::GenericException& exception) {
      std::cerr << exception.GetDescription() << std::endl;
    }

    return nullptr;
  }

} // namespace camio
