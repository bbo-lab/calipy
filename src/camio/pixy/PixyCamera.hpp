#pragma once

#include "../Camera.hpp"

#include <pixyhandle.hpp>

namespace camio {
  class PixyCamera : public Camera {
  public:
    PixyCamera(PixyHandle h);
    ~PixyCamera();

    TriggerMode getTrigger();
    bool setTrigger(TriggerMode mode);

    double getFrameRate();
    bool setFrameRate(double hz);

    double getExposure();
    bool setExposure(double ms);

    Size getFrameSize();

    bool start();

    bool stop();

    Frame* grab();

  private:
    PixyHandle _handle;

    TriggerMode _mode;

    Size _size;
  };
}
