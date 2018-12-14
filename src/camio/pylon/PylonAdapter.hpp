#pragma once

#include "../Adapter.hpp"

#include <pylon/PylonIncludes.h>

namespace camio {
  class PylonAdapter : public Adapter {
  public:
    static std::string version();

    PylonAdapter();
    virtual ~PylonAdapter();

    virtual std::vector<CameraInfo> enumerate();

    virtual Camera* open(std::string id);
  };
}
