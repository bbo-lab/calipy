#include "PixyCamera.hpp"

#include <iostream>

#include "PixyAdapter.hpp"


static inline void debayer(uint16_t width, uint16_t x, uint16_t y, uint8_t *pixel, uint8_t* r, uint8_t* g, uint8_t* b) {
    if (y&1) {
        if (x&1) {
            *r = *pixel;
            *g = (*(pixel-1)+*(pixel+1)+*(pixel+width)+*(pixel-width))>>2;
            *b = (*(pixel-width-1)+*(pixel-width+1)+*(pixel+width-1)+*(pixel+width+1))>>2;
        } else {
            *r = (*(pixel-1)+*(pixel+1))>>1;
            *g = *pixel;
            *b = (*(pixel-width)+*(pixel+width))>>1;
        }
    } else {
        if (x&1) {
            *r = (*(pixel-width)+*(pixel+width))>>1;
            *g = *pixel;
            *b = (*(pixel-1)+*(pixel+1))>>1;
        } else {
            *r = (*(pixel-width-1)+*(pixel-width+1)+*(pixel+width-1)+*(pixel+width+1))>>2;
            *g = (*(pixel-1)+*(pixel+1)+*(pixel+width)+*(pixel-width))>>2;
            *b = *pixel;
        }
    }
}


namespace camio {

  PixyCamera::PixyCamera(PixyHandle h)
    :_handle(h), _mode(Software), _size(318, 198) {

    // Disable onboard processing
    int32_t response;
    int return_value = _handle.command("stop", END_OUT_ARGS, &response, END_IN_ARGS);

    if(return_value != 0 or response != 0) {
      std::cerr << "Failed to stop processing" << std::endl;
    }

    if(_handle.led_set_RGB(0, 255, 0) != 0)
      std::cerr << "[camio] set led failed" << std::endl;
  }

  PixyCamera::~PixyCamera() {
    _handle.led_set_RGB(0, 0, 0);
    _handle.close();
  }

  Camera::TriggerMode PixyCamera::getTrigger() {
    return _mode;
  }
  bool PixyCamera::setTrigger(TriggerMode mode) {
    return (_mode == Software);
  }

  double PixyCamera::getFrameRate() {
    return 0.0;
  }
  bool PixyCamera::setFrameRate(double hz) {
    return false;
  }

  double PixyCamera::getExposure() {
    return 0.0;
  }
  bool PixyCamera::setExposure(double ms) {
    return false;
  }

  Size PixyCamera::getFrameSize() {
    return _size;
  }

  bool PixyCamera::start() {
    return false;
  }

  bool PixyCamera::stop() {
    return false;
  }

  Frame* PixyCamera::grab() {

    uint8_t* buffer; // Chirp buffer, available till next chirp call
    int32_t response, fourcc;
    int8_t renderflags;
    uint16_t width, height;
    uint32_t  length;

    response = 0;
    int status = _handle.command("cam_getFrame",
                                 INT8(0x21),     // mode
                                 INT16(0),       // xoffset
                                 INT16(0),       // yoffset
                                 INT16(320),     // width
                                 INT16(200),     // height
                                 END_OUT_ARGS,
                                 &response,
                                 &fourcc,
                                 &renderflags,
                                 &width,
                                 &height,
                                 &length,
                                 &buffer,
                                 END_IN_ARGS);
    if(response != 0 or status != 0) {
      std::cerr << "Failed to grab frame " << response << " " << PixyAdapter::errorstring(status) << std::endl;
    }

    // Remove unusable pixels on side, debayer and convert.
    Frame* result = new Frame(width - 2, height - 2);

    // Skip first row
    buffer += width;

    uint8_t* line = result->data;
    for (int y = 1; y < height - 1; y++) {
      buffer++; // Skip first column
      for (int x = 1; x < width - 1; x++, buffer++) {
        // Debayer image ...
        uint8_t r, g, b;
        debayer(width, x, y, buffer, &r, &g, &b);
        // ... and convert to grayscale
        *line++ = 0.299f * r + 0.587f * g + 0.114f * b;
      }
      buffer++; // Skip last column
    }
    return result;
  }
}
