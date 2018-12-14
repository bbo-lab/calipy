#pragma once

#include "../Adapter.hpp"

namespace camio {
  class DummyAdapter : public Adapter {
  public:
    static std::string version();

    DummyAdapter();

    std::vector<CameraInfo> enumerate();

    Camera* open(std::string);
  };
}
