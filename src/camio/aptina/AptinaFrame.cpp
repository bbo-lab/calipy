#include "AptinaFrame.hpp"

namespace camio {
  const int AptinaFrame::ADDITIONAL_PIXEL = 512;

  size_t AptinaSize::pixels() {
    return Size::pixels() + AptinaFrame::ADDITIONAL_PIXEL;
  }

  AptinaFrame::AptinaFrame(Size s) {
    width = s.width;
    height = s.height;
    data = new uint8_t[(width * height) + ADDITIONAL_PIXEL];
  }

  AptinaFrame::~AptinaFrame() {
    delete[] data;
  }

  Size AptinaFrame::size() {
    return AptinaSize(width, height);
  }

}
