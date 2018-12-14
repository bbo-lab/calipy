#pragma once

#include "../Camera.hpp"

#include <apbase.h>

#include "AptinaFrame.hpp"

namespace camio {
  class AptinaCamera : public Camera {
  public:
    static const int MAX_TRIES;

    static const int MIN_HORZ_BLANK;
    static const int MAX_HORZ_BLANK;

    static const int MIN_VERT_BLANK;

    AptinaCamera(AP_HANDLE handle);
    ~AptinaCamera();

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
    bool setRegister(const char* reg, const char* bits, uint32_t value, int32_t expected = AP_FLAG_OK, bool check_value = true);
    uint32_t getRegister(const char* reg, const char* bits);

    bool setMode(const char* name, uint32_t value);
    uint32_t getMode(const char* name);

    bool useMasterMode();
    bool useSnapshotMode();

    bool useLVDS();

    void setLock(bool state);
    bool getLock();

    uint32_t getRowPixels();

    bool setExposurePixels(uint32_t p);
    uint32_t getExposurePixels(bool overhead = false);

    uint32_t getFramePixels();

    AP_HANDLE _handle;

    TriggerMode _mode;

    AptinaSize _size;

    uint32_t _pixel_clock;
  };
}
