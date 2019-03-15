#pragma once

#include "Frame.hpp"

namespace camio {
  class Camera {
  public:
    enum TriggerMode {
        Software, // Camera is triggered on grab
        Timer, // Camera is triggered by hardware timer at framerate
        External // Camera is triggered by external source (like other camera)
    };

    virtual ~Camera() {};

    virtual TriggerMode getTrigger() = 0;
    virtual bool setTrigger(TriggerMode mode) = 0;

    virtual double getFrameRate() = 0;
    virtual bool setFrameRate(double hz) = 0;

    virtual double getExposure() = 0;
    virtual bool setExposure(double ms) = 0;

    virtual Size getFrameSize() = 0;

    /// Start frame acquisition
    virtual bool start() = 0;

    /// Stop frame acquisiton
    virtual bool stop() = 0;

    /// Grab next frame
    virtual Frame* grab() = 0;

  protected:
    Camera() {}

  private:
    // Disable copying
    Camera(Camera const &) = delete;
    void operator=(Camera const &) = delete;
  };
}
