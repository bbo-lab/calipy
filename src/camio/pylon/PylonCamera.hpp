#include "../Camera.hpp"

//#include <pylon/PylonIncludes.h>
#include <pylon/Platform.h>
#include <pylon/usb/BaslerUsbInstantCamera.h>

namespace camio {
  class PylonCamera : public Camera, public Pylon::CBaslerUsbInstantCamera { /// FixMe: Support more then USB TL
  public:
    PylonCamera(Pylon::IPylonDevice* dev);
    ~PylonCamera();

    Camera::TriggerMode getTrigger();
    bool setTrigger(Camera::TriggerMode mode);

    double getFrameRate();
    bool setFrameRate(double hz);

    double getExposure();
    bool setExposure(double ms);

    Size getFrameSize();

    bool start();
    bool stop();

    Frame* grab();

  private:
    bool useTimerTrigger();
    bool useSoftwareTrigger();
    bool useExternalTrigger();

    bool enableTriggerOut();
    bool enableExposureOut();

    Camera::TriggerMode _mode;
  };
}
