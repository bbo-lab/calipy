#pragma once

#include <string>
#include <vector>

#include "Camera.hpp"

namespace camio {

  struct CameraInfo {
    std::string id;
    std::string name;
    std::string description;
  };

  class Adapter {
  public:
    virtual ~Adapter() {}

    virtual std::vector<CameraInfo> enumerate() = 0;

    virtual Camera* open(std::string id) = 0;
  };
}
