#include "DummyAdapter.hpp"

#include "DummyCamera.hpp"

namespace camio {
  std::string DummyAdapter::version() {
    return "libdummy v0.0.0";
  }

  DummyAdapter::DummyAdapter() {}

  std::vector<CameraInfo> DummyAdapter::enumerate() {
    CameraInfo info;

    info.id = "SN-DUMMY-SN";
    info.name = "Dummy Camera";
    info.description = "Not real, just a dummy";

    std::vector<CameraInfo> vec;
    vec.push_back(info);

    return vec;
  }

  Camera* DummyAdapter::open(std::string) {
    return new DummyCamera;
  }

} // namespace camio
