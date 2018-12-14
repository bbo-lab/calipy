#pragma once

#include "../Adapter.hpp"

namespace camio {
  class PixyAdapter : public Adapter {
  public:
    static std::string version();

    static std::string errorstring(int e);

    PixyAdapter();
    ~PixyAdapter();

    std::vector<CameraInfo> enumerate();

    Camera* open(std::string id);
  };
}
