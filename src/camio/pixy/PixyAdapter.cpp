#include "PixyAdapter.hpp"

#include <iostream>
#include <sstream>
#include <vector>

#include "pixy.h"
#include <pixyhandle.hpp>

#include "PixyCamera.hpp"

namespace camio {
  std::string PixyAdapter::version() {
    return std::string("libpixyusb ") + pixy_library_version();
  }

  std::string PixyAdapter::errorstring(int error) {
    for(int i = 0; i < NUM_PIXY_ERRORS; i++) {

      // Skip empty rows
      if(!PIXY_ERROR_TABLE[i].text) continue;

      // Check for error code
      if(PIXY_ERROR_TABLE[i].error == error) {
        return PIXY_ERROR_TABLE[i].text;
      }
    }
    return "undefined error";
  }

  PixyAdapter::PixyAdapter() {}

  PixyAdapter::~PixyAdapter() {
  }

  std::vector<CameraInfo> PixyAdapter::enumerate() {
    std::vector<CameraInfo> devices;

    int num_pixies = PixyHandle::num_pixies_attached();

    int index = 0;
    std::vector<PixyHandle>  handles(num_pixies);
    for(auto h : handles) {
      CameraInfo info;

      int init_status = h.init();
      if(init_status != 0) {
        std::cerr << "[camio] init failed: " << errorstring(init_status) << std::endl;
        continue;
      }

      // Get firmware version
      uint16_t major, minor, build;
      int fw_status = h.get_firmware_version(&major, &minor, &build);
      if(fw_status != 0) {
        std::cerr << "[camio] get firmware version failed: " << errorstring(fw_status) << std::endl;
        continue;
      }
      std::stringstream version;
      version << "firmware v" << major << "." << minor << "." << build;

      uint32_t uid = 0;
      int cmd_status = h.command("getUID", END_OUT_ARGS, &uid, END_IN_ARGS);
      if(cmd_status != 0) {
        std::cerr << "[camio] get UID failed: " << errorstring(cmd_status) << std::endl;
        continue;
      }

      info.id   = std::to_string(uid);
      info.name = "Pixy (CMUcam5)";
      info.description = version.str();

      devices.push_back(info);

      h.led_set_RGB(255, 0, 0);
      index++;
    }

    for(auto h : handles) {
      h.close();
    }

    return devices;
  }

  Camera* PixyAdapter::open(std::string id) {
    int count = PixyHandle::num_pixies_attached();

    std::vector<PixyHandle>  handles(count);
    for(int i = 0; i < count; i++) {
      if(handles[i].init() != 0) continue;

      uint32_t uid;
      if(handles[i].command("getUID", END_OUT_ARGS, &uid, END_IN_ARGS) != 0) continue;

      if(std::to_string(uid) == id) {
        // Close all previous handles
        for(int j = 0; j < i; j++) {
          handles[j].close();
        }
        return new PixyCamera(handles[i]);
      }
    }

    // No camera found
    for(auto h : handles) {
      h.close();
    }

    return nullptr;
  }

}
