#include "PylonFrame.hpp"

namespace camio {

  PylonFrame::PylonFrame(Pylon::CGrabResultPtr ptr)
    : _ptr(ptr) {
    width  = ptr->GetWidth(),
    height = ptr->GetHeight(),
      data   = static_cast<uint8_t*>(ptr->GetBuffer());
  }

}// namespace camio
