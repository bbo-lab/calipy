#include "../Frame.hpp"

#include <pylon/PylonIncludes.h>

namespace camio {
  class PylonFrame : public Frame {
  public:
    PylonFrame(Pylon::CGrabResultPtr image);

  private:
    Pylon::CGrabResultPtr _ptr;
  };
}
