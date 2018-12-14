#include "AptinaCamera.hpp"

#include <unistd.h>
#include <iostream>
#include <cmath>

#include "AptinaFrame.hpp"
#include "aptina.hpp"

namespace camio {
  const int AptinaCamera::MAX_TRIES = 3;

  const int AptinaCamera::MIN_HORZ_BLANK = 61; // from data sheet
  const int AptinaCamera::MAX_HORZ_BLANK = 1023; // from midilib

  const int AptinaCamera::MIN_VERT_BLANK = 4; // from data sheet

  AptinaCamera::AptinaCamera(AP_HANDLE h)
    : _handle(h), _mode(Timer), _size(0, 0), _pixel_clock(0) {

    if(!_handle) {
      std::cerr << "Invalid handle" << std::endl;
      return;
    }

    // Reset sensor
    // ToDo: Check if this does anything using LVDS
    setMode("sensor_reset", 1);
    usleep(500);

    // Set i2c speed to 100 kHz
    setMode("ship_speed", 100);

    // Get pixel clock
    _pixel_clock = getMode("pixclk_freq");

    // Stop streaming of data
    stop();

    // Connnect via lvds (default for now)
    useLVDS();

    // Disble auto exposure
    setRegister("auto_block_control", "aec_enable_contexta", 0);
    setRegister("auto_block_control", "agch_enable_contexta", 0);

    // Disable unswizzle
    setMode("unswizzle_mode", 0);

    // Always use context A
    setRegister("control_mode_reg", "contextb_enable", 0);

    // Set up frame dimesions
    int32_t status;

    status = ap_SetImageFormat(_handle, 0, 0, "BAYER-8");
    if(status != AP_CAMERA_SUCCESS)
      std::cerr << "[camio] set format failed" << aptina::errorstring(status) << std::endl;

    status = ap_GetImageFormat(_handle, (uint32_t*) &_size.width, (uint32_t*) &_size.height, nullptr, 0);
    if(_size.pixels() == 0) //ToDo: Check why status != AP_CAMERA_SUCCESS does not work
      std::cerr << "[camio] get format failed " << aptina::errorstring(status) << std::endl;

    // Check recommended buffer size
    if(ap_GrabFrame(_handle, NULL, 0) != _size.pixels()) {
      std::cerr << "camio error: Unknown recommended buffer size" << std::endl;
    }
  }

  AptinaCamera::~AptinaCamera() {
    ap_Destroy(_handle);
  }

  Camera::TriggerMode AptinaCamera::getTrigger() {
    return _mode;
  }

  bool AptinaCamera::setTrigger(Camera::TriggerMode mode) {
    if(mode == _mode)
      return true;

    switch(mode) {
      case Timer:
        return useMasterMode();
      case External:
        return useSnapshotMode();
      default:
        std::cerr << "camio error: Trigger mode not supported" << std::endl;
        return false;
    }
  }

  double AptinaCamera::getFrameRate() {
    if(_mode != Timer) return 0.0;

    double pixels = std::max(getFramePixels(), getExposurePixels(true));

    return _pixel_clock / pixels;
  }

  bool AptinaCamera::setFrameRate(double hz) {
    // Only timer mode supports a fixed framerate
    if(_mode != Timer) return false;

    // Save current exposure
    uint32_t exposure = getExposurePixels();

    // Warn about the physically impossible
    if(exposure > _pixel_clock / hz) {
      std::cerr << "[camio] Exposure to long to support framerate" << std::endl;
    }

    // Adjust blanking to closely match frame time by ...
    int pixels = std::round(_pixel_clock / hz) - 4;

    int v_min = std::ceil((pixels / ((double) _size.width + MAX_HORZ_BLANK)) - _size.height);
    int v_max = std::floor((pixels / ((double) _size.width + MIN_HORZ_BLANK)) - _size.height);

    // ... finding closed grid point to hyperbolic min func
    uint32_t vert_blank, horz_blank;
    int error = pixels;
    for(int v = std::max(v_min, MIN_VERT_BLANK); v < v_max; v++) {
      int h = std::round((pixels / ((double) _size.height + v)) - _size.width);
      int p = (_size.width + h) * (_size.height + v);
      int e = std::abs(pixels - p);
      if(e < error) {
        error = e;
        vert_blank = v;
        horz_blank = h;
      }
    }

    bool result = true;
    // Send new values to sensor
    result &= setRegister("horz_blank_contexta_reg", "", horz_blank);
    result &= setRegister("vert_blank_contexta_reg", "", vert_blank);

    // Restore exposure based on new frame timing
    result &= setExposurePixels(exposure);

    return result;
  }


  double AptinaCamera::getExposure() {
    return (getExposurePixels() * 1000.0) / _pixel_clock; // ms
  }

  bool AptinaCamera::setExposure(double ms) {
    uint32_t pixels = std::round(ms * _pixel_clock / 1000);

    return setExposurePixels(pixels);
  }


  Frame* AptinaCamera::grab() {
    Frame* frame = new AptinaFrame(_size);

    size_t length = 0;
    do {
      length = ap_GrabFrame(_handle, frame->data, _size.pixels());
    } while (ap_GetLastError() == AP_NOT_ENOUGH_DATA_ERROR);

    if(length != _size.pixels() and (length + AptinaFrame::ADDITIONAL_PIXEL) != _size.pixels()) {
      std::cerr << "[camio] missing frame data: " << _size.pixels() - length << std::endl;
    }

    if(ap_GetLastError() != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] grab returned " << aptina::lasterrorstring() << std::endl;
      delete frame;
      return nullptr;
    }

    return frame;
  }


  Size AptinaCamera::getFrameSize() {
    return _size;
  }


  bool AptinaCamera::start() {
    mi_camera_t* cam = ap_GetMidlibCamera(_handle);

    // Reset frame buffer?
    //setMode(HW_BUFFERING, 1);
    //setMode(HW_BUFFERING, 3); MI_RESET_IMAGE_FIFO


    // Enable streaming
    //mi_startTransport(cam);

    //setLock(true);
    return true;
  }

  bool AptinaCamera::stop() {
    //setLock(false);
    //mi_stopTransport(ap_GetMidlibCamera(_handle));
    return true;
  }


  bool AptinaCamera::useMasterMode() {
    setRegister("control_mode_reg", "operating_mode", 1);
    setRegister("control_mode_reg", "simultaneous_seq", 1);

    return true;
  }

  bool AptinaCamera::useSnapshotMode() {
    bool result = true;

    result &= setRegister("control_mode_reg", "operating_mode", 3);
    result &= setRegister("control_mode_reg", "simultaneous_seq", 1); // Does nothing...

    // Use minimum blanking, to support max framerate
    result &= setRegister("vert_blank_contexta_reg", "", MIN_VERT_BLANK);
    result &= setRegister("horz_blank_contexta_reg", "", MIN_HORZ_BLANK);

    return result;
  }


  bool AptinaCamera::useLVDS() {
    bool result = true;

    // Pwr-off LVDS data receiver
    //setRegister("lvds_data_control", "powerdown", 1);

    // Make sure we use 8bit mode
    result &= setRegister("lvds_use_10bit_pixels", "", 0);

    // Pwr-on LVDS clock
    result &= setRegister("lvds_shft_clk_control", "powerdown", 0);

    // Pwr-on LVDS master (PLL + LVDS drivers)
    result &= setRegister("lvds_master_control", "lvds_powerdown", 0);

    // Issue soft reset
    result &= setRegister("reset_reg", "soft_reset", 1, AP_FLAG_PAUSE, false);

    // Issue an lvds sync
    result &= setRegister("lvds_internal_sync", "", 1, AP_FLAG_RESUME);
    result &= setRegister("lvds_internal_sync", "", 0, AP_FLAG_RESUME);

    return result;
  }

  uint32_t AptinaCamera::getRowPixels() {
    uint32_t horz_blank = getRegister("horz_blank_contexta_reg", "");
    return _size.width + horz_blank;
  }

  bool AptinaCamera::setExposurePixels(uint32_t pixels) {
    uint32_t row_pixels = getRowPixels();

    uint32_t coarse_width = pixels / row_pixels;
    uint32_t fine_width = pixels - (coarse_width * row_pixels);

    bool result = true;
    result &= setRegister("coarse_shutter_width_total_contexta", "", coarse_width);
    result &= setRegister("fine_shutter_width_total_contexta", "", fine_width);
    return result;
  }

  uint32_t AptinaCamera::getExposurePixels(bool overhead) {
    uint32_t coarse_width = getRegister("coarse_shutter_width_total_contexta", "");
    uint32_t fine_width = getRegister("fine_shutter_width_total_contexta", "");

    if(overhead) coarse_width += 2; // See data sheet "Output Data Timing"

    return coarse_width * getRowPixels() + fine_width + 4;
  }

  uint32_t AptinaCamera::getFramePixels() {
    uint32_t vert_blank = getRegister("vert_blank_contexta_reg", "");

    return (_size.height + vert_blank) * getRowPixels() + 4;
  }


  void AptinaCamera::setLock(bool state) {
    uint32_t page = 0; // CORE addr space
    uint32_t addr = 0xFE;
    uint32_t width = 8;

    int32_t effect = AP_FLAG_OK;

    uint32_t value = state ? 0xDEAD : 0xBEEF;

    int32_t result = ap_SetSensorRegisterAddr(_handle, MI_REG_ADDR, page, addr, width, value, &effect);

    if(result != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] failed to lock registers:" << aptina::errorstring(result) << std::endl;
    }

    if(effect != AP_FLAG_OK) {
      std::cerr << "[camio] lock caused side effect: " << aptina::effectstring(effect) << std::endl;
    }

    if(state != getLock()) {
      std::cerr << "[camio] Failed change lock state to " << (state ? "true" : "false")  << std::endl;
    }
  }

  bool AptinaCamera::getLock() {
    uint32_t page = 0; // CORE addr space
    uint32_t addr = 0xFE;
    uint32_t width = 8;

    bool cached = false;

    uint32_t value = 0;

    int32_t result = ap_GetSensorRegisterAddr(_handle, MI_REG_ADDR, page, addr, width, &value, cached);

    if(result != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] failed to lock registers:" << aptina::errorstring(result) << std::endl;
    }

    switch(value) {
      case 0xDEAD:
        return true;
    case 0xDEAF:
      std::cerr << "[camio] partial lock detected, but not supported" << std::endl;
      return false;
    case 0xBEEF:
      return false;
    default:
      std::cerr << "[camio] Unknown lock state: " << std::hex << value << std::endl;
    }
    return false;
  }


  bool AptinaCamera::setRegister(const char* reg, const char* bits, uint32_t value, int32_t expected, bool check_value) {
    int tries = 0;
    do {
      int32_t effect = AP_FLAG_OK;
      int32_t result = ap_SetSensorRegister(_handle, reg, bits, value, &effect);

      if(result != AP_CAMERA_SUCCESS) {
        std::cerr << "[camio] failed to set register '" << reg << "' '" << bits << "': " << aptina::errorstring(result) << std::endl;
      }

      if(ap_GetLastError() != AP_CAMERA_SUCCESS) {
        std::cerr << "[camio2] failed to set register '" << reg << "' '" << bits << "': " << aptina::lasterrorstring() << std::endl;
      }

      // Check if caller expected side effect
      if(effect != expected) {
        std::cerr << "[camio] unexpected side effect '" << reg << "' '" << bits << "': " << aptina::effectstring(effect) << std::endl;
      }

      tries++;
      usleep(50000);
    } while(check_value and getRegister(reg, bits) != value and tries != MAX_TRIES); /// ToDo: Add retry on error?

    // Check if tries were exceded
    if(tries == MAX_TRIES) {
      std::cerr << "[camio] failed to set '" << reg << "' '" << bits << "' after " << tries << " attempts." << std::endl;
      return false;
    }
    return true;
  }

  uint32_t AptinaCamera::getRegister(const char* reg, const char* bits) {
    uint32_t value = 0;
    bool cached = false;
    int32_t result = ap_GetSensorRegister(_handle, reg, bits, &value, cached);

    if(result != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] failed to get register '" << reg << "' '" << bits << "': " << aptina::errorstring(result) << std::endl;
    }

    return value;
  }


  bool AptinaCamera::setMode(const char* name, uint32_t value) {
    int32_t result = ap_SetMode(_handle, name, value);

    if(result != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] failed to set mode '" << name << "': " << aptina::errorstring(result) << std::endl;
      return false;
    }
    return true;
  }

  uint32_t AptinaCamera::getMode(const char* name) {
    uint32_t value = ap_GetMode(_handle, name);

    if(ap_GetLastError() != AP_CAMERA_SUCCESS) {
      std::cerr << "[camio] failed to get mode '" << name << "': " << aptina::lasterrorstring() << std::endl;
    }

    return value;
  } 
}
