#pragma once

#include "../Adapter.hpp"

namespace camio {
  class AptinaAdapter : public Adapter {
  public:
    static std::string version();

    AptinaAdapter();
    ~AptinaAdapter();

    std::vector<CameraInfo> enumerate(); 

    Camera* open(std::string id);
  };
}
