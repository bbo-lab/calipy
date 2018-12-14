#include "camio.hpp"

#include <iostream>

#ifdef CAMIO_WITH_DUMMY
  #include "dummy/DummyAdapter.hpp"
#endif

#ifdef CAMIO_WITH_PYLON
  #include "pylon/PylonAdapter.hpp"
#endif

#ifdef CAMIO_WITH_APTINA
  #include "aptina/AptinaAdapter.hpp"
#endif

#ifdef CAMIO_WITH_PIXY
  #include "pixy/PixyAdapter.hpp"
#endif


namespace camio {
 static std::map<AdapterID, Adapter*> CAMIO_ADAPTER_INSTANCES;

  CameraHandle::CameraHandle(AdapterID adapter, const CameraInfo info)
    : adapter(adapter) {
    id = info.id;
    name = info.name;
    description = info.description;
  }

  std::vector<std::string> versions() {
    std::vector<std::string> versions;

    versions.push_back("libcamio v0.0.1");

#ifdef CAMIO_WITH_DUMMY
    versions.push_back(DummyAdapter::version());
#endif

#ifdef CAMIO_WITH_APTINA
    versions.push_back(AptinaAdapter::version());
#endif

#ifdef CAMIO_WITH_PYLON
    versions.push_back(PylonAdapter::version());
#endif

#ifdef CAMIO_WITH_PIXY
    versions.push_back(PixyAdapter::version());
#endif

    return versions;
  }

  void initialize(AdapterID id) {
    switch(id) {
#ifdef CAMIO_WITH_DUMMY
    case AdapterID::DUMMY:
      CAMIO_ADAPTER_INSTANCES[AdapterID::DUMMY] = new DummyAdapter;
      break;
#endif
#ifdef CAMIO_WITH_APTINA
    case AdapterID::APTINA:
      CAMIO_ADAPTER_INSTANCES[AdapterID::APTINA] = new AptinaAdapter;
      break;
#endif
#ifdef CAMIO_WITH_PYLON
    case AdapterID::PYLON:
      CAMIO_ADAPTER_INSTANCES[AdapterID::PYLON] = new PylonAdapter;
      break;
#endif
#ifdef CAMIO_WITH_PIXY
    case AdapterID::PIXY:
      CAMIO_ADAPTER_INSTANCES[AdapterID::PIXY] = new PixyAdapter;
      break;
#endif
    default:
      std::cerr << "WARNING: Unknown or not supported adapter" << std::endl;
    }
  }

  void initializeAll() {
#ifdef CAMIO_WITH_DUMMY
    initialize(AdapterID::DUMMY);
#endif

#ifdef CAMIO_WITH_APTINA
    initialize(AdapterID::APTINA);
#endif

#ifdef CAMIO_WITH_PYLON
    initialize(AdapterID::PYLON);
#endif

#ifdef CAMIO_WITH_PIXY
    initialize(AdapterID::PIXY);
#endif
  }

  std::vector<CameraHandle> enumerate() {
    std::vector<CameraHandle> cams;

    for(auto& kv : CAMIO_ADAPTER_INSTANCES) {
      for(auto& info : kv.second->enumerate()) {
        cams.push_back(CameraHandle(kv.first, info));
      }
    }

    return cams;
  }

  Camera* open(AdapterID a_id, std::string c_id) {
    return CAMIO_ADAPTER_INSTANCES[a_id]->open(c_id);
  }

  Camera* open(CameraHandle info) {
    return open(info.adapter, info.id);
  }

} // namespace camio
