#include "PylonCamera.hpp"

#include "PylonFrame.hpp"

namespace camio {

  PylonCamera::PylonCamera(Pylon::IPylonDevice* dev)
    : Pylon::CBaslerUsbInstantCamera(dev),
      _mode(Timer) {
    Open();

    // Sensible defaults
    ExposureAuto.SetValue(Basler_UsbCameraParams::ExposureAuto_Off);

    PixelFormat.SetValue(Basler_UsbCameraParams::PixelFormat_Mono8);
    AcquisitionMode.SetValue(Basler_UsbCameraParams::AcquisitionMode_Continuous);
    ShutterMode.SetValue(Basler_UsbCameraParams::ShutterMode_Global);

    enableExposureOut();
    useTimerTrigger();
  }

  PylonCamera::~PylonCamera(){
    Close();
  }


  Camera::TriggerMode PylonCamera::getTrigger() {
    return _mode;
  }

  bool PylonCamera::setTrigger(Camera::TriggerMode mode) {
    if(mode == _mode) return true;

    switch(mode) {
      case Software:
        enableTriggerOut();
        return useSoftwareTrigger();
      case Timer:
        enableTriggerOut();
        return useTimerTrigger();
      case External:
        return useExternalTrigger();
      default:
        std::cerr << "camio error: Unknown mode" << std::endl;
        return false;
    }

  }


  double PylonCamera::getFrameRate() {
    return AcquisitionFrameRate.GetValue();
  }

  bool PylonCamera::setFrameRate(double hz) {
    try {
      AcquisitionFrameRate.SetValue(hz);
    } catch (const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
      return false;
    }
    return true;
  }


  double PylonCamera::getExposure() {
    return ExposureTime.GetValue() / 1000.0;
  }

  bool PylonCamera::setExposure(double ms) {
    try {
      ExposureTime.SetValue(ms * 1000.0);
    } catch (const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
      return false;
    }
    return true;
  }


  Size PylonCamera::getFrameSize() {
    return Size(Width.GetValue(), Height.GetValue());
  }


  bool PylonCamera::start() {
    try {
      StartGrabbing();
    } catch (const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
      return false;
    }
    return true;
  }

  bool PylonCamera::stop() {
    try {
      StopGrabbing();
    } catch (const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
      return false;
    }
    return true;
  }


  Frame* PylonCamera::grab() {
    try {
      Pylon::CGrabResultPtr result;

      if(_mode == Software) {
        // Trigger camera
        WaitForFrameTriggerReady(50, Pylon::TimeoutHandling_ThrowException);
        ExecuteSoftwareTrigger();
      }

      // Retrieve Frame
      RetrieveResult(50, result, Pylon::TimeoutHandling_ThrowException);

      return new PylonFrame(result);

    } catch (const Pylon::GenericException& exception) {
      std::cerr << "camio error: " << exception.GetDescription() << std::endl;
    }
    return nullptr;
  }


  bool PylonCamera::useTimerTrigger() {
    CUsbCameraParams_Params::TriggerMode.SetValue(Basler_UsbCameraParams::TriggerMode_Off);
    AcquisitionFrameRateEnable.SetValue(true);

    return true;
  }

  bool PylonCamera::useSoftwareTrigger() {
    TriggerSelector.SetValue(Basler_UsbCameraParams::TriggerSelector_FrameStart);
    TriggerSource.SetValue(Basler_UsbCameraParams::TriggerSource_Software);

    return true;
  }

  bool PylonCamera::useExternalTrigger() {
    // Use falling edge on line 3 as trigger
    CUsbCameraParams_Params::TriggerMode.SetValue(Basler_UsbCameraParams::TriggerMode_On);
    TriggerSource.SetValue(Basler_UsbCameraParams::TriggerSource_Line3);
    TriggerActivation.SetValue(Basler_UsbCameraParams::TriggerActivation_FallingEdge);
    TriggerSelector.SetValue(Basler_UsbCameraParams::TriggerSelector_FrameStart);

    return true;
  }

  bool PylonCamera::enableTriggerOut() {
    // Output exposure signal as trigger on putput 3
    LineSelector.SetValue(Basler_UsbCameraParams::LineSelector_Line3);
    LineMode.SetValue(Basler_UsbCameraParams::LineMode_Output);
    LineSource.SetValue(Basler_UsbCameraParams::LineSource_ExposureActive);

    return true;
  }

  bool PylonCamera::enableExposureOut() {
    // Output exposure signal on putput 4
    LineSelector.SetValue(Basler_UsbCameraParams::LineSelector_Line4);
    LineMode.SetValue(Basler_UsbCameraParams::LineMode_Output);
    LineSource.SetValue(Basler_UsbCameraParams::LineSource_ExposureActive);

    return true;
  }
} // namespace camio
