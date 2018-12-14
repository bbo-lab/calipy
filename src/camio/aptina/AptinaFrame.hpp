#pragma once

#include "../Frame.hpp"

namespace camio {
  // Just like the normal size, but with extra pixels
  struct AptinaSize : public Size {
    using Size::Size;
    size_t pixels();
  };

  // Just like the normal frame but with 512 extra pixels
  struct AptinaFrame : public Frame {
    static const int ADDITIONAL_PIXEL;

    AptinaFrame(Size s);
    ~AptinaFrame();

    Size size() ;
  };
}
