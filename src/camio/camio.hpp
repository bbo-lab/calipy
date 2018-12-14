#pragma once

#include <map>

#include "Adapter.hpp"

namespace camio {
  enum class AdapterID {
    DUMMY,
    APTINA,
    PYLON,
    PIXY,
  };

  struct CameraHandle : public CameraInfo {
    CameraHandle(AdapterID adapter, const CameraInfo info);

    AdapterID adapter;
  };

  std::vector<std::string> versions();

  void initialize(AdapterID id);

  void initializeAll();

  std::vector<CameraHandle> enumerate();

  Camera* open(AdapterID a_id, std::string c_id);

  Camera* open(CameraHandle info);
}
