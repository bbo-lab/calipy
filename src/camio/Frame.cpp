#include "Frame.hpp"

namespace camio {

  Size::Size(size_t w, size_t h)
    : width(w), height(h) {}

  size_t Size::pixels() {
    return width * height;
  }

  Frame::Frame()
    : width(0),
      height(0),
      data(nullptr),
      _free_data_in_dtor(false) {
  }

  Frame::Frame(Size s)
      : Frame(s.width, s.height) {}

  Frame::Frame(size_t w, size_t h)
    : width(w),
      height(h),
      data(nullptr),
      _free_data_in_dtor(true) {
    data = new uint8_t[w * h];
  }

  Frame::~Frame() {
    if(_free_data_in_dtor) delete[] data;
  }

  uint8_t& Frame::at(size_t x, size_t y) {
    return data[y * width + x];
  }

  Size Frame::size() {
    return Size(width, height);
  }
}
