#pragma once

#include <cstddef>
#include <cstdint>

namespace camio {

  struct Size {
    Size(size_t w, size_t h);

    virtual size_t pixels();

    size_t width;
    size_t height;
  };

  // Container for single frame, for now considered row major.
  struct Frame {
    Frame(Size size);
    Frame(size_t width, size_t height);
    virtual ~Frame();

    // x is column, y is row because this is a row major image.
    uint8_t& at(size_t x, size_t y);

    virtual Size size();

    size_t width;
    size_t height;

    uint8_t* data;

  protected:
    Frame();

  private:
    // True, if data should be free in dtor
    bool _free_data_in_dtor;
  };
}
