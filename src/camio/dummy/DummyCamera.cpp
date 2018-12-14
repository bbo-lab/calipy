#include "DummyCamera.hpp"

namespace camio {

  DummyCamera::DummyCamera() {}


  Camera::TriggerMode DummyCamera::getTrigger() {
    return Software;
  }

  bool DummyCamera::setTrigger(Camera::TriggerMode mode){
    return (mode != Software);
  }


  double DummyCamera::getFrameRate(){
    return 0.0;
  }

  bool DummyCamera::setFrameRate(double hz){
    return false;
  }


  double DummyCamera::getExposure(){
    return 0.0;
  }

  bool DummyCamera::setExposure(double ms){
    return false;
  }


  Size DummyCamera::getFrameSize(){
    return Size(640, 480);
  }


  bool DummyCamera::start() {
    return true;
  }

  bool DummyCamera::stop() {
    return true;
  }


  Frame* DummyCamera::grab() {
    Frame* frame = new Frame(640, 480);

    // Generate gradient from left to right, that switches direction in the middle
    for(int x = 0; x < 640; x++) {
      for(int y = 0; y < 480; y++) {
        if(y < 240) {
          frame->at(x, y) = x / 2.5;
        } else {
          frame->at(x, y) = (640 - x) / 2.5;
        }
      }
    }

    return frame;
  }

}
