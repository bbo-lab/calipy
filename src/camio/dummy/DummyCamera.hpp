#include "../Camera.hpp"


namespace camio {
  class DummyCamera : public Camera {
  public:
    DummyCamera();

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
  };
}
